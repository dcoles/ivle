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
import datetime

import cjson
import pg

import ivle.database
from ivle import (util, chat, caps)
from ivle.conf import (usrmgt_host, usrmgt_port, usrmgt_magic)
import ivle.pulldown_subj

from ivle.rpc.decorators import require_method, require_cap

from ivle.auth import AuthError, authenticate
import urllib

# The user must send this declaration message to ensure they acknowledge the
# TOS
USER_DECLARATION = "I accept the IVLE Terms of Service"

# List of fields returned as part of the user JSON dictionary
# (as returned by the get_user action)
user_fields_list = (
    "login", "state", "unixid", "email", "nick", "fullname",
    "rolenm", "studentid", "acct_exp", "pass_exp", "last_login",
    "svn_pass"
)

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

@require_method('POST')
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
    try:
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
        try:
            # Check that the user's status is "no_agreement".
            # (Both to avoid redundant calls, and to stop disabled users from
            # re-enabling their accounts).
            if req.user.state != "no_agreement":
                req.throw_error(req.HTTP_BAD_REQUEST,
                "You have already agreed to the terms.")
            # Write state "pending" to ensure we don't try this again
            req.user.state = u"pending"
        except:
            req.store.rollback()
            raise
        req.store.commit()

        # Get the arguments for usermgt.activate_user from the session
        # (The user must have already logged in to use this app)
        args = {
            "login": req.user.login,
        }
        msg = {'activate_user': args}

        # Release our lock on the db so usrmgt can write
        req.store.rollback()

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
            req.user.state = u"enabled"
        else:
            # Reset the user back to no agreement
            req.user.state = u"no_agreement"
            req.store.commit()

        # Write the response
        req.content_type = "text/plain"
        req.write(cjson.encode(response))
    except:
        req.store.rollback()
        raise

create_user_fields_required = [
    'login', 'fullname', 'rolenm'
]
create_user_fields_optional = [
    'password', 'nick', 'email', 'studentid'
]

@require_method('POST')
@require_cap(caps.CAP_UPDATEUSER)
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

    user = ivle.database.User(**create)
    req.store.add(user)
    ivle.pulldown_subj.enrol_user(req.store, user)
    req.store.commit()

    req.content_type = "text/plain"
    req.write(str(user.unixid))

update_user_fields_anyone = [
    'password', 'nick', 'email'
]
update_user_fields_admin = [
    'password', 'nick', 'email', 'rolenm', 'unixid', 'fullname',
    'studentid'
]

@require_method('POST')
def handle_update_user(req, fields):
    """Update a user's account details.
    This can be done in a limited form by any user, on their own account,
    or with full powers by a user with CAP_UPDATEUSER on any account.
    """
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

    user = ivle.database.User.get_by_login(req.store, login)

    oldpassword = fields.getfirst('oldpass')
    if oldpassword is not None: # It was specified.
        oldpassword = oldpassword.value

    # If the user is trying to set a new password, check that they have
    # entered old password and it authenticates.
    if fields.getfirst('password') is not None:
        try:
            authenticate.authenticate(req.store, login, oldpassword)
        except AuthError:
            req.headers_out['X-IVLE-Action-Error'] = \
                urllib.quote("Old password incorrect.")
            req.status = req.HTTP_BAD_REQUEST
            # Cancel all the changes made to user (including setting new pass)
            req.store.rollback()
            return

    # Make a dict of fields to update
    for f in fieldlist:
        val = fields.getfirst(f)
        if val is not None:
            # Note: May be rolled back if auth check below fails
            setattr(user, f, val.value.decode('utf-8'))
        else:
            pass

    req.store.commit()

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
    userobj = ivle.database.User.get_by_login(req.store, login)
    user = ivle.util.object_to_dict(user_fields_list, userobj)
    # Convert time stamps to nice strings
    for k in 'pass_exp', 'acct_exp', 'last_login':
        if user[k] is not None:
            user[k] = unicode(user[k])

    user['local_password'] = userobj.passhash is not None

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
        user = ivle.database.User.get_by_login(req.store,
                    fields.getfirst('login'))
        if user is None:
            raise AttributeError()
        if not fullpowers and user != req.user:
            # Not allowed to edit other users
            req.throw_error(req.HTTP_FORBIDDEN,
            "You do not have permission to see another user's subjects.")
    except AttributeError:
        # If login not specified, update yourself
        user = req.user

    dict_enrolments = []
    for e in user.active_enrolments:
        dict_enrolments.append({
            'offeringid':      e.offering.id,
            'subj_code':       e.offering.subject.code,
            'subj_name':       e.offering.subject.name,
            'subj_short_name': e.offering.subject.short_name,
            'url':             e.offering.subject.url,
            'year':            e.offering.semester.year,
            'semester':        e.offering.semester.semester,
            'groups':          [{'name': group.name,
                                 'nick': group.nick} for group in e.groups]
        })
    response = cjson.encode(dict_enrolments)
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

    subject = req.store.get(ivle.database.Subject, subjectid)

    response = cjson.encode([{'offeringid': offering.id,
                              'subj_name': offering.subject.name,
                              'year': offering.semester.year,
                              'semester': offering.semester.semester,
                              'active': offering.semester.active
                             } for offering in subject.offerings
                                    if offering.semester.active])
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

    offering = req.store.get(ivle.database.Offering, offeringid)

    dict_projectsets = []
    try:
        for p in offering.project_sets:
            dict_projectsets.append({
                'projectsetid': p.id,
                'max_students_per_group': p.max_students_per_group,
                'groups': [{'groupid': g.id,
                            'groupnm': g.name,
                            'nick': g.nick} for g in p.project_groups]
            })
    except Exception, e:
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR, repr(e))

    response = cjson.encode(dict_projectsets)
    req.write(response)

@require_method('POST')
@require_cap(caps.CAP_MANAGEGROUPS)
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
    # Get required fields
    projectsetid = fields.getfirst('projectsetid').value
    groupnm = fields.getfirst('groupnm').value
    if projectsetid is None or groupnm is None:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "Required: projectsetid, groupnm")
    groupnm = unicode(groupnm)
    try:
        projectsetid = int(projectsetid)
    except:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "projectsetid must be an int")
    # Get optional fields
    nick = fields.getfirst('nick').value
    if nick is not None:
        nick = unicode(nick)

    # Begin transaction since things can go wrong
    try:
        group = ivle.database.ProjectGroup(name=groupnm,
                                           project_set_id=projectsetid,
                                           nick=nick,
                                           created_by=req.user,
                                           epoch=datetime.datetime.now())
        req.store.add(group)

        # Create the group repository
        # Yes, this is ugly, and it would be nice to just pass in the groupid,
        # but the object isn't visible to the extra transaction in
        # usrmgt-server until we commit, which we only do once the repo is
        # created.
        offering = group.project_set.offering

        args = {
            "subj_short_name": offering.subject.short_name,
            "year": offering.semester.year,
            "semester": offering.semester.semester,
            "groupnm": group.name,
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
        req.store.commit()

    except Exception, e:
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR, repr(e))

    req.content_type = "text/plain"
    req.write('')

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
    group = req.store.get(ivle.database.ProjectGroup, groupid)

    try:
        offeringid = int(offeringid)
    except:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "offeringid must be an int")
    offering = req.store.get(ivle.database.Offering, offeringid)


    offeringmembers = [{'login': user.login,
                        'fullname': user.fullname
                       } for user in offering.members.order_by(
                            ivle.database.User.login)
                      ]
    groupmembers = [{'login': user.login,
                        'fullname': user.fullname
                       } for user in group.members.order_by(
                            ivle.database.User.login)
                      ]

    # Make sure we don't include members in both lists
    for member in groupmembers:
        if member in offeringmembers:
            offeringmembers.remove(member)

    response = cjson.encode(
        {'groupmembers': groupmembers, 'available': offeringmembers})

    req.content_type = "text/plain"
    req.write(response)

@require_method('POST')
@require_cap(caps.CAP_MANAGEGROUPS)
def handle_assign_group(req, fields):
    """ Required cap: CAP_MANAGEGROUPS
    Assigns a user to a project group
    Required:
        login, groupid
    """
    # Get required fields
    login = fields.getfirst('login')
    groupid = fields.getfirst('groupid')
    if login is None or groupid is None:
        req.throw_error(req.HTTP_BAD_REQUEST,
            "Required: login, groupid")

    group = req.store.get(ivle.database.ProjectGroup, int(groupid))
    user = ivle.database.User.get_by_login(req.store, login)

    # Add membership to database
    # We can't keep a transaction open until the end here, as usrmgt-server
    # needs to see the changes!
    try:
        group.members.add(user)
        req.store.commit()

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
    "create_group": handle_create_group,
    "assign_group": handle_assign_group,
}
