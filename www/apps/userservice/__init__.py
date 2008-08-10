# IVLE
# Copyright (C) 2007-2008 The University of Melbourne
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# App: userservice
# Author: Matt Giuca
# Date: 14/2/2008

# Provides an Ajax service for handling user management requests.
# This includes when a user logs in for the first time.

# NOTE: This app does NOT require authentication. This is because otherwise it
# would be blocked from receiving requests to activate when the user is trying
# to accept the TOS.

# It must do its own authentication and authorization.

### Actions ###

# The one-and-only path segment to userservice determines the action being
# undertaken.
# All actions require that you are logged in.
# All actions require method = POST, unless otherwise stated.

# userservice/activate_me
# Required cap: None
# declaration = "I accept the IVLE Terms of Service"
# Activate the currently-logged-in user's account. Requires that "declaration"
# is as above, and that the user's state is "no_agreement".

# userservice/create_user
# Required cap: CAP_CREATEUSER
# Arguments are the same as the database columns for the "login" table.
# Required:
#   login, fullname, rolenm
# Optional:
#   password, nick, email, studentid

# userservice/get_user
# method: May be GET
# Required cap: None to see yourself.
#   CAP_GETUSER to see another user.
# Gets the login details of a user. Returns as a JSON object.
# login = Optional login name of user to get. If omitted, get yourself.

# userservice/update_user
# Required cap: None to update yourself.
#   CAP_UPDATEUSER to update another user (and also more fields).
#   (This is all-powerful so should be only for admins)
# login = Optional login name of user to update. If omitted, update yourself.
# Other fields are optional, and will set the given field of the user.
# Without CAP_UPDATEUSER, you may change the following fields of yourself:
#   password, nick, email
# With CAP_UPDATEUSER, you may also change the following fields of any user:
#   password, nick, email, login, rolenm, unixid, fullname, studentid
# (You can't change "state", but see userservice/[en|dis]able_user).

# TODO
# userservice/enable_user
# Required cap: CAP_UPDATEUSER
# Enable a user whose account has been disabled. Does not work for
# no_agreement or pending users.
# login = Login name of user to enable.

# TODO
# userservice/disable_user
# Required cap: CAP_UPDATEUSER
# Disable a user's account. Does not work for no_agreement or pending users.
# login = Login name of user to disable.

# userservice/get_enrolments
# Required cap: None (for yourself)
# Returns a JSON encoded listing of a students is enrollments

# userservice/get_active_offerings(req, fields):
# Required cap: None
# Returns all the active offerings for a particular subject
# Required:
#   subjectid

# PROJECTS AND GROUPS

# userservice/get_project_groups
# Required cap: None
# Returns all the project groups in an offering grouped by project set
# Required:
#   offeringid

# userservice/create_project_set
# Required cap: CAP_MANAGEPROJECTS
# Creates a project set for a offering
# Required:
#   offeringid, max_students_per_group
# Returns:
#   projectsetid

# userservice/create_project
# Required cap: CAP_MANAGEPROJECTS
# Creates a project in a specific project set
# Required:
#   projectsetid
# Optional:
#   synopsis, url, deadline
# Returns:
#   projectid

# userservice/create_group
# Required cap: CAP_MANAGEGROUPS
# Creates a project group in a specific project set
# Required:
#   projectsetid, groupnm
# Optional:
#   nick

# userservice/get_group_membership
# Required cap: None
# Returns two lists. One of people in the group and one of people not in the 
# group (but enroled in the offering)
# Required:
#   groupid

# userservice/assign_to_group
# Required cap: CAP_MANAGEGROUPS
# Assigns a user to a project group
# Required: login, groupid

import os
import sys
import time

import cjson
import pg

import common
import common.db
import common.makeuser
from common import (util, chat, caps)
import conf

from conf import (usrmgt_host, usrmgt_port, usrmgt_magic)

# The user must send this declaration message to ensure they acknowledge the
# TOS
USER_DECLARATION = "I accept the IVLE Terms of Service"

def handle(req):
    """Handler for the Console Service AJAX backend application."""
    if req.user is None:
        # Not logged in
        req.throw_error(req.HTTP_FORBIDDEN,
        "You are not logged in to IVLE.")
    if len(req.path) > 0 and req.path[-1] == os.sep:
        path = req.path[:-1]
    else:
        path = req.path
    # The path determines which "command" we are receiving
    fields = req.get_fieldstorage()
    try:
        func = actions_map[req.path]
    except KeyError:
        req.throw_error(req.HTTP_BAD_REQUEST,
        "%s is not a valid userservice action." % repr(req.path))
    func(req, fields)

def handle_activate_me(req, fields):
    """Create the jail, svn, etc, for the currently logged in user (this is
    put in the queue for usermgt to do).
    This will block until usermgt returns, which could take seconds to minutes
    in the extreme. Therefore, it is designed to be called by Ajax, with a
    nice "Please wait" message on the frontend.

    This will signal that the user has accepted the terms of the license
    agreement, and will result in the user's database status being set to
    "enabled". (Note that it will be set to "pending" for the duration of the
    handling).

    As such, it takes a single POST field, "declaration", which
    must have the value, "I accept the IVLE Terms of Service".
    (Otherwise users could navigate to /userservice/createme without
    "accepting" the terms - at least this way requires them to acknowledge
    their acceptance). It must only be called through a POST request.
    """
    db = common.db.DB()
    try:
        if req.method != "POST":
            req.throw_error(req.HTTP_METHOD_NOT_ALLOWED,
            "Only POST requests are valid methods to activate_me.")
        try:
            declaration = fields.getfirst('declaration')
        except AttributeError:
            declaration = None      # Will fail next test
        if declaration != USER_DECLARATION:
            req.throw_error(req.HTTP_BAD_REQUEST,
            "Please use the Terms of Service form instead of talking to "
            "this service directly.")

        # Make sure the user's status is "no_agreement", and set status to
        # pending, within the one transaction. This ensures we only do this
        # one time.
        db.start_transaction()
        try:

            user_details = db.get_user(req.user.login)
            # Check that the user's status is "no_agreement".
            # (Both to avoid redundant calls, and to stop disabled users from
            # re-enabling their accounts).
            if user_details.state != "no_agreement":
                req.throw_error(req.HTTP_BAD_REQUEST,
                "You have already agreed to the terms.")
            # Write state "pending" to ensure we don't try this again
            db.update_user(req.user.login, state="pending")
        except:
            db.rollback()
            raise
        db.commit()

        # Get the arguments for usermgt.activate_user from the session
        # (The user must have already logged in to use this app)
        args = {
            "login": req.user.login,
        }
        msg = {'activate_user': args}

        # Try and contact the usrmgt server
        try:
            response = chat.chat(usrmgt_host, usrmgt_port, msg, usrmgt_magic)
        except cjson.DecodeError:
            # Gave back rubbish - set the response to failure
            response = {'response': 'usrmgt-failure'}

        # Get the staus of the users request
        try:
            status = response['response']
        except KeyError:
            status = 'failure'
        
        if status == 'okay':
            req.user.state = "enabled"
        else:
            # Reset the user back to no agreement
            req.user.state = "no_agreement"
            db.update_user(req.user.login, state="no_agreement")


        # Update the users state
        session = req.get_session()
        session['user'] = req.user
        session.save()

        # Write the response
        req.content_type = "text/plain"
        req.write(cjson.encode(response))
    finally:
        db.close()

create_user_fields_required = [
    'login', 'fullname', 'rolenm'
]
create_user_fields_optional = [
    'password', 'nick', 'email', 'studentid'
]
def handle_create_user(req, fields):
    """Create a new user, whose state is no_agreement.
    This does not create the user's jail, just an entry in the database which
    allows the user to accept an agreement.
       Expected fields:
        login       - used as a unix login name and svn repository name.
                      STRING REQUIRED 
        password    - the clear-text password for the user. If this property is
                      absent or None, this is an indication that external
                      authentication should be used (i.e. LDAP).
                      STRING OPTIONAL
        email       - the user's email address.
                      STRING OPTIONAL
        nick        - the display name to use.
                      STRING REQUIRED
        fullname    - The name of the user for results and/or other official
                      purposes.
                      STRING REQUIRED
        rolenm      - The user's role. Must be one of "anyone", "student",
                      "tutor", "lecturer", "admin".
                      STRING/ENUM REQUIRED
        studentid   - If supplied and not None, the student id of the user for
                      results and/or other official purposes.
                      STRING OPTIONAL
       Return Value: the uid associated with the user. INT
    """
    if req.method != "POST":
        req.throw_error(req.HTTP_METHOD_NOT_ALLOWED,
            "Only POST requests are valid methods to create_user.")
    # Check if this user has CAP_UPDATEUSER
    if not req.user.hasCap(caps.CAP_UPDATEUSER):
        req.throw_error(req.HTTP_FORBIDDEN,
        "You do not have permission to create users.")

    # Make a dict of fields to create
    create = {}
    for f in create_user_fields_required:
        val = fields.getfirst(f)
        if val is not None:
            create[f] = val
        else:
            req.throw_error(req.HTTP_BAD_REQUEST,
            "Required field %s missing." % repr(f))
    for f in create_user_fields_optional:
        val = fields.getfirst(f)
        if val is not None:
            create[f] = val
        else:
            pass

    common.makeuser.make_user_db(**create)
    user = common.db.DB().get_user(create["login"])
    req.content_type = "text/plain"
    req.write(str(user.unixid))

update_user_fields_anyone = [
    'password', 'nick', 'email'
]
update_user_fields_admin = [
    'password', 'nick', 'email', 'rolenm', 'unixid', 'fullname',
    'studentid'
]
def handle_update_user(req, fields):
    """Update a user's account details.
    This can be done in a limited form by any user, on their own account,
    or with full powers by a user with CAP_UPDATEUSER on any account.
    """
    if req.method != "POST":
        req.throw_error(req.HTTP_METHOD_NOT_ALLOWED,
        "Only POST requests are valid methods to update_user.")

    # Only give full powers if this user has CAP_UPDATEUSER
    fullpowers = req.user.hasCap(caps.CAP_UPDATEUSER)
    # List of fields that may be changed
    fieldlist = (update_user_fields_admin if fullpowers
        else update_user_fields_anyone)

    try:
        login = fields.getfirst('login')
        if login is None:
            raise AttributeError()
        if not fullpowers and login != req.user.login:
            # Not allowed to edit other users
            req.throw_error(req.HTTP_FORBIDDEN,
            "You do not have permission to update another user.")
    except AttributeError:
        # If login not specified, update yourself
        login = req.user.login

    # Make a dict of fields to update
    update = {}
    for f in fieldlist:
        val = fields.getfirst(f)
        if val is not None:
            update[f] = val
        else:
            pass
    update['login'] = login

    db = common.db.DB()
    db.update_user(**update)

    # Re-read the user's details from the DB so we can update their session
    # XXX potentially-unsafe session write
    if login == req.user.login:
        user = db.get_user(login)
        session = req.get_session()
        session['user'] = user
        session.save()

    db.close()

    req.content_type = "text/plain"
    req.write('')

def handle_get_user(req, fields):
    """
    Retrieve a user's account details. This returns all details which the db
    module is willing to give up, EXCEPT the following fields:
        svn_pass
    """
    # Only give full powers if this user has CAP_GETUSER
    fullpowers = req.user.hasCap(caps.CAP_GETUSER)

    try:
        login = fields.getfirst('login')
        if login is None:
            raise AttributeError()
        if not fullpowers and login != req.user.login:
            # Not allowed to edit other users
            req.throw_error(req.HTTP_FORBIDDEN,
            "You do not have permission to see another user.")
    except AttributeError:
        # If login not specified, update yourself
        login = req.user.login

    # Just talk direct to the DB
    db = common.db.DB()
    user = db.get_user(login)
    db.close()
    user = dict(user)
    if 'role' in user:
        user['rolenm'] = str(user['role'])
        del user['role']
    try:
        del user['svn_pass']
    except KeyError:
        pass
    # Convert time stamps to nice strings
    try:
        if user['pass_exp'] is not None:
            user['pass_exp'] = str(user['pass_exp'])
    except KeyError:
        pass
    try:
        if user['acct_exp'] is not None:
            user['acct_exp'] = str(user['acct_exp'])
    except KeyError:
        pass
    try:
        if user['last_login'] is not None:
            user['last_login'] = str(user['last_login'])
    except KeyError:
        pass
    response = cjson.encode(user)
    req.content_type = "text/plain"
    req.write(response)

def handle_get_enrolments(req, fields):
    """
    Retrieve a user's enrolment details. Each enrolment includes any group
    memberships for that offering.
    """
    # For the moment we're only able to query ourselves
    fullpowers = False
    ## Only give full powers if this user has CAP_GETUSER
    ##fullpowers = req.user.hasCap(caps.CAP_GETUSER)

    try:
        login = fields.getfirst('login')
        if login is None:
            raise AttributeError()
        if not fullpowers and login != req.user.login:
            # Not allowed to edit other users
            req.throw_error(req.HTTP_FORBIDDEN,
            "You do not have permission to see another user's subjects.")
    except AttributeError:
        # If login not specified, update yourself
        login = req.user.login

    # Just talk direct to the DB
    db = common.db.DB()
    enrolments = db.get_enrolment(login)
    for e in enrolments:
        e['groups'] = db.get_enrolment_groups(login, e['offeringid'])
    db.close()
    response = cjson.encode(enrolments)
    req.content_type = "text/plain"
    req.write(response)

def handle_get_active_offerings(req, fields):
    """Required cap: None
    Returns all the active offerings for a particular subject
    Required:
        subjectid
    """

    subjectid = fields.getfirst('subjectid')
    if subjectid is None:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "Required: subjectid")
    try:
        subjectid = int(subjectid)
    except:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "subjectid must be a integer")
    
    db = common.db.DB()
    try:
        offerings = db.get_offering_semesters(subjectid)
    finally:
        db.close()

    response = cjson.encode([o for o in offerings if o['active']])
    req.content_type = "text/plain"
    req.write(response)

def handle_get_project_groups(req, fields):
    """Required cap: None
    Returns all the project groups in an offering grouped by project set
    Required:
        offeringid
    """

    offeringid = fields.getfirst('offeringid')
    if offeringid is None:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "Required: offeringid")
    try:
        offeringid = int(offeringid)
    except:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "offeringid must be a integer")
    
    db = common.db.DB()
    try:
        projectsets = db.get_projectsets_by_offering(offeringid)
        for p in projectsets:
            p['groups'] = db.get_groups_by_projectset(p['projectsetid'])
    except Exception, e:
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR, repr(e))
    finally:
        db.close()

    response = cjson.encode(projectsets)
    req.write(response)

def handle_create_project_set(req, fields):
    """Required cap: CAP_MANAGEPROJECTS
    Creates a project set for a offering - returns the projectsetid
    Required:
        offeringid, max_students_per_group
    """
    
    if req.method != "POST":
        req.throw_error(req.HTTP_METHOD_NOT_ALLOWED,
            "Only POST requests are valid methods to create_user.")
    # Check if this user has CAP_MANAGEPROJECTS
    if not req.user.hasCap(caps.CAP_MANAGEPROJECTS):
        req.throw_error(req.HTTP_FORBIDDEN,
        "You do not have permission to manage projects.")
    # Get required fields
    offeringid = fields.getfirst('offeringid')
    max_students_per_group = fields.getfirst('max_students_per_group')
    if offeringid is None or max_students_per_group is None:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "Required: offeringid, max_students_per_group")

    # Talk to the DB
    db = common.db.DB()
    dbquery = db.return_insert(
        {
            'offeringid': offeringid,
            'max_students_per_group': max_students_per_group,
        },
        "project_set",
        frozenset(["offeringid", "max_students_per_group"]),
        ["projectsetid"],
    )
    db.close()
    
    response = cjson.encode(dbquery.dictresult()[0])

    req.content_type = "text/plain"
    req.write(response)

def handle_create_project(req, fields):
    """Required cap: CAP_MANAGEPROJECTS
    Creates a project in a specific project set
    Required:
        projectsetid
    Optional:
        synopsis, url, deadline
    Returns:
        projectid
    """
    
    if req.method != "POST":
        req.throw_error(req.HTTP_METHOD_NOT_ALLOWED,
            "Only POST requests are valid methods to create_user.")
    # Check if this user has CAP_MANAGEPROJECTS
    if not req.user.hasCap(caps.CAP_MANAGEPROJECTS):
        req.throw_error(req.HTTP_FORBIDDEN,
        "You do not have permission to manage projects.")
    # Get required fields
    projectsetid = fields.getfirst('projectsetid')
    if projectsetid is None:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "Required: projectsetid")
    # Get optional fields
    synopsis = fields.getfirst('synopsis')
    url = fields.getfirst('url')
    deadline = fields.getfirst('deadline')
    if deadline is not None:
        try:
            deadline = util.parse_iso8601(deadline).timetuple()
        except ValueError, e:
            req.throw_error(req.HTTP_BAD_REQUEST, e.message)

    # Talk to the DB
    db = common.db.DB()
    try:
        dbquery = db.return_insert(
            {
                'projectsetid': projectsetid,
                'synopsis': synopsis,
                'url': url,
                'deadline': deadline,
            },
            "project", # table
            frozenset(["projectsetid", "synopsis", "url", "deadline"]),
            ["projectid"], # returns
        )
    except Exception, e:
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR, repr(e))
    finally:
        db.close()
    
    response = cjson.encode(dbquery.dictresult()[0])

    req.content_type = "text/plain"
    req.write(response)

def handle_create_group(req, fields):
    """Required cap: CAP_MANAGEGROUPS
    Creates a project group in a specific project set
    Required:
        projectsetid, groupnm
    Optional:
        nick
    Returns:
        groupid
    """
    if req.method != "POST":
        req.throw_error(req.HTTP_METHOD_NOT_ALLOWED,
            "Only POST requests are valid methods to create_user.")
    # Check if this is allowed to manage groups
    if not req.user.hasCap(caps.CAP_MANAGEGROUPS):
        req.throw_error(req.HTTP_FORBIDDEN,
        "You do not have permission to manage groups.")
    # Get required fields
    projectsetid = fields.getfirst('projectsetid')
    groupnm = fields.getfirst('groupnm')
    if projectsetid is None or groupnm is None:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "Required: projectsetid, groupnm")
    try:
        projectsetid = int(projectsetid)
    except:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "projectsetid must be an int")
    # Get optional fields
    nick = fields.getfirst('nick')

    # Talk to the DB
    db = common.db.DB()
    # Other fields
    createdby = db.get_user_loginid(req.user.login)
    epoch = time.localtime()

    # Begin transaction since things can go wrong
    db.start_transaction()
    try:
        dbquery = db.return_insert(
            {
                'groupnm': groupnm,
                'projectsetid': projectsetid,
                'nick': nick,
                'createdby': createdby,
                'epoch': epoch,
            },
            "project_group", # table
            frozenset(["groupnm", "projectsetid", "nick", "createdby",
                "epoch"]), # fields
            ["groupid"], # returns
        )
 
        singlerow = dbquery.dictresult()[0]
        groupid = singlerow['groupid']

        # Create the groups repository
        # Get the arguments for usermgt.activate_user from the session
        # (The user must have already logged in to use this app)
    
        # Find the rest of the parameters we need
        offeringinfo = db.get_offering_info(projectsetid)
                
        subj_short_name = offeringinfo['subj_short_name']
        year = offeringinfo['year']
        semester = offeringinfo['semester']

        args = {
            "subj_short_name": subj_short_name,
            "year": year,
            "semester": semester,
            "groupnm": groupnm,
        }
        msg = {'create_group_repository': args}

        # Contact the usrmgt server
        try:
            usrmgt = chat.chat(usrmgt_host, usrmgt_port, msg, usrmgt_magic)
        except cjson.DecodeError, e:
            req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR,
                "Could not understand usrmgt server response: %s"%e.message)

        if 'response' not in usrmgt or usrmgt['response']=='failure':
            req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR,
                "Failure creating repository: %s"%str(usrmgt))
    
        # Everything went OK. Lock it in
        db.commit()

    except Exception, e:
        db.rollback()
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR, repr(e))
    finally:
        db.close()

    response = cjson.encode(singlerow)

    req.content_type = "text/plain"
    req.write(response)

def handle_get_group_membership(req, fields):
    """ Required cap: None
    Returns two lists. One of people in the group and one of people not in the 
    group (but enroled in the offering)
    Required:
        groupid, offeringid
    """
    # Get required fields
    groupid = fields.getfirst('groupid')
    offeringid = fields.getfirst('offeringid')
    if groupid is None or offeringid is None:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "Required: groupid, offeringid")
    try:
        groupid = int(groupid)
    except:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "groupid must be an int")
    try:
        offeringid = int(offeringid)
    except:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "offeringid must be an int")

    db = common.db.DB()
    try:
        offeringmembers = db.get_offering_members(offeringid)
        groupmembers = db.get_projectgroup_members(groupid)
    finally:
        db.close()
    
    # Make sure we don't include members in both lists
    for member in groupmembers:
        if member in offeringmembers:
            offeringmembers.remove(member)

    response = cjson.encode(
        {'groupmembers': groupmembers, 'available': offeringmembers})

    req.content_type = "text/plain"
    req.write(response)

def handle_assign_group(req, fields):
    """ Required cap: CAP_MANAGEGROUPS
    Assigns a user to a project group
    Required:
        login, groupid
    """
    if req.method != "POST":
        req.throw_error(req.HTTP_METHOD_NOT_ALLOWED,
            "Only POST requests are valid methods to create_user.")
    # Check if this user is allowed to manage groups
    if not req.user.hasCap(caps.CAP_MANAGEGROUPS):
        req.throw_error(req.HTTP_FORBIDDEN,
        "You do not have permission to manage groups.")
    # Get required fields
    login = fields.getfirst('login')
    groupid = fields.getfirst('groupid')
    if login is None or groupid is None:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "Required: login, groupid")
    groupid = int(groupid)

    # Talk to the DB
    db = common.db.DB()
    try:
        loginid = db.get_user_loginid(login)
    except common.db.DBException, e:
        req.throw_error(req.HTTP_BAD_REQUEST, repr(e))

    # Add assignment to database
    # We can't use a transaction here, as usrmgt-server needs to see the
    # changes!
    try:
        dbquery = db.insert(
            {
                'loginid': loginid,
                'groupid': groupid,
            },
            "group_member", # table
            frozenset(["loginid", "groupid"]), # fields
        )

        # Rebuild the svn config file
        # Contact the usrmgt server
        msg = {'rebuild_svn_group_config': {}}
        try:
            usrmgt = chat.chat(usrmgt_host, usrmgt_port, msg, usrmgt_magic)
        except cjson.DecodeError, e:
            req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR,
                "Could not understand usrmgt server response: %s"%e.message)

            if 'response' not in usrmgt or usrmgt['response']=='failure':
                req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR,
                    "Failure creating repository: %s"%str(usrmgt))
    except Exception, e:
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR, repr(e))
    finally:
        db.close()

    return(cjson.encode({'response': 'okay'}))

# Map action names (from the path)
# to actual function objects
actions_map = {
    "activate_me": handle_activate_me,
    "create_user": handle_create_user,
    "update_user": handle_update_user,
    "get_user": handle_get_user,
    "get_enrolments": handle_get_enrolments,
    "get_active_offerings": handle_get_active_offerings,
    "get_project_groups": handle_get_project_groups,
    "get_group_membership": handle_get_group_membership,
    "create_project_set": handle_create_project_set,
    "create_project": handle_create_project,
    "create_group": handle_create_group,
    "assign_group": handle_assign_group,
}
