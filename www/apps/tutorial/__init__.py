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

# App: tutorial
# Author: Matt Giuca
# Date: 25/1/2008

# Tutorial application.
# Displays tutorial content with editable exercises, allowing students to test
# and submit their solutions to exercises and have them auto-tested.

# URL syntax
# All path segments are optional (omitted path segments will show menus).
# The first path segment is the subject code.
# The second path segment is the worksheet name.

import os
import os.path
from datetime import datetime
import cgi
import urllib
import re
from xml.dom import minidom
import mimetypes

import cjson

from ivle import util
import ivle.conf
import ivle.database
import ivle.worksheet

from rst import rst

import genshi
import genshi.core
import genshi.template

THIS_APP = "tutorial"

# Regex for valid identifiers (subject/worksheet names)
re_ident = re.compile("[0-9A-Za-z_]+")

class Worksheet:
    def __init__(self, id, name, assessable):
        self.id = id
        self.name = name
        self.assessable = assessable
        self.loc = urllib.quote(id)
        self.complete_class = ''
        self.optional_message = ''
        self.total = 0
        self.mand_done = 0
    def __repr__(self):
        return ("Worksheet(id=%s, name=%s, assessable=%s)"
                % (repr(self.id), repr(self.name), repr(self.assessable)))

def make_tutorial_path(subject=None, worksheet=None):
    """Creates an absolute (site-relative) path to a tutorial sheet.
    Subject or worksheet can be None.
    Ensures that top-level or subject-level URLs end in a '/', because they
    are represented as directories.
    """
    if subject is None:
        return util.make_path(THIS_APP + '/')
    else:
        if worksheet is None:
            return util.make_path(os.path.join(THIS_APP, subject + '/'))
        else:
            return util.make_path(os.path.join(THIS_APP, subject, worksheet))

def handle(req):
    """Handler for the Tutorial application."""

    # TODO: Take this as an argument instead (refactor dispatch)
    ctx = genshi.template.Context()

    # Set request attributes
    req.content_type = "text/html"
    req.scripts = [
        "media/common/util.js",
        "media/common/json2.js",
        "media/tutorial/tutorial.js",
    ]
    req.styles = [
        "media/tutorial/tutorial.css",
    ]
    # Note: Don't print write_html_head_foot just yet
    # If we encounter errors later we do not want this

    path_segs = req.path.split('/')
    subject = None
    worksheet = None
    if len(req.path) > 0:
        subject = path_segs[0]
        if subject == "media":
            # Special case: "tutorial/media" will plainly serve any path
            # relative to "subjects/media".
            handle_media_path(req)
            return
        if len(path_segs) > 2:
            req.throw_error(req.HTTP_NOT_FOUND,
                "Invalid tutorial path.")
        if len(path_segs) == 2:
            worksheet = path_segs[1]

    if subject == None:
        ctx['whichmenu'] = 'toplevel'
        handle_toplevel_menu(req, ctx)
    elif worksheet == None:
        ctx['whichmenu'] = 'subjectmenu'
        handle_subject_menu(req, ctx, subject)
    else:
        ctx['whichmenu'] = 'worksheet'
        handle_worksheet(req, ctx, subject, worksheet)

    # Use Genshi to render out the template
    # TODO: Dispatch should do this instead
    loader = genshi.template.TemplateLoader(".", auto_reload=True)
    tmpl = loader.load(util.make_local_path("apps/tutorial/template.html"))
    req.write(tmpl.generate(ctx).render('html')) #'xhtml', doctype='xhtml'))

def handle_media_path(req):
    """
    Urls in "tutorial/media" will just be served directly, relative to
    subjects. So if we came here, we just want to serve a file relative to the
    subjects directory on the local file system.
    """
    # First normalise the path
    urlpath = os.path.normpath(req.path)
    # Now if it begins with ".." or separator, then it's illegal
    if urlpath.startswith("..") or urlpath.startswith('/'):
        req.throw_error(req.HTTP_FORBIDDEN,
            "Invalid path.")
    filename = os.path.join(ivle.conf.subjects_base, urlpath)
    (type, _) = mimetypes.guess_type(filename)
    if type is None:
        type = ivle.conf.mimetypes.default_mimetype
    ## THIS CODE taken from apps/server/__init__.py
    if not os.access(filename, os.R_OK):
        req.throw_error(req.HTTP_NOT_FOUND,
            "The requested file does not exist.")
    if os.path.isdir(filename):
        req.throw_error(req.HTTP_FORBIDDEN,
            "The requested file is a directory.")
    req.content_type = type
    req.sendfile(filename)

def handle_toplevel_menu(req, ctx):
    # This is represented as a directory. Redirect and add a slash if it is
    # missing.
    if req.uri[-1] != '/':
        req.throw_redirect(make_tutorial_path())
    req.write_html_head_foot = True

    ctx['enrolled_subjects'] = req.user.subjects
    ctx['unenrolled_subjects'] = [subject for subject in
                           req.store.find(ivle.database.Subject)
                           if subject not in ctx['enrolled_subjects']]

def is_valid_subjname(subject):
    m = re_ident.match(subject)
    return m is not None and m.end() == len(subject)

def handle_subject_menu(req, ctx, subject):
    # This is represented as a directory. Redirect and add a slash if it is
    # missing.
    if req.uri[-1] != '/':
        req.throw_redirect(make_tutorial_path(subject))
    # Subject names must be valid identifiers
    if not is_valid_subjname(subject):
        req.throw_error(req.HTTP_NOT_FOUND,
            "Invalid subject name: %s." % repr(subject))
    # Parse the subject description file
    # The subject directory must have a file "subject.xml" in it,
    # or it does not exist (404 error).

    ctx['subject'] = subject
    try:
        subjectfile = open(os.path.join(ivle.conf.subjects_base, subject,
            "subject.xml")).read()
    except:
        req.throw_error(req.HTTP_NOT_FOUND,
            "Subject %s not found." % repr(subject))

    subjectfile = genshi.Stream(list(genshi.XML(subjectfile)))

    ctx['worksheets'] = get_worksheets(subjectfile)
    
    # Now all the errors are out the way, we can begin writing

    req.write_html_head_foot = True
    # As we go, calculate the total score for this subject
    # (Assessable worksheets only, mandatory problems only)
    problems_done = 0
    problems_total = 0
    for worksheet_from_xml in ctx['worksheets']:
        worksheet = ivle.database.Worksheet.get_by_name(req.store,
            subject, worksheet_from_xml.id)
        # If worksheet is not in database yet, we'll simply not display
        # data about it yet (it should be added as soon as anyone visits
        # the worksheet itself).
        if worksheet is not None:
            # If the assessable status of this worksheet has changed,
            # update the DB
            # (Note: This fails the try block if the worksheet is not yet
            # in the DB, which is fine. The author should visit the
            # worksheet page to get it into the DB).
            if worksheet.assessable != worksheet_from_xml.assessable:
                # XXX If statement to avoid unnecessary database writes.
                # Is this necessary, or will Storm check for us?
                worksheet.assessable = worksheet_from_xml.assessable
                req.store.commit()
            if worksheet.assessable:
                # Calculate the user's score for this worksheet
                mand_done, mand_total, opt_done, opt_total = (
                    ivle.worksheet.calculate_score(req.store, req.user,
                        worksheet))
                if opt_total > 0:
                    optional_message = " (excluding optional exercises)"
                else:
                    optional_message = ""
                if mand_done >= mand_total:
                    worksheet.complete_class = "complete"
                elif mand_done > 0:
                    worksheet.complete_class = "semicomplete"
                else:
                    worksheet.complete_class = "incomplete"
                problems_done += mand_done
                problems_total += mand_total
                worksheet.mand_done = mand_done
                worksheet.total = mand_total
                worksheet.optional_message = optional_message

    ctx['problems_total'] = problems_total
    ctx['problems_done'] = problems_done
    if problems_total > 0:
        if problems_done >= problems_total:
            ctx['complete_class'] = "complete"
        elif problems_done > 0:
            ctx['complete_class'] = "semicomplete"
        else:
            ctx['complete_class'] = "incomplete"
        ctx['problems_pct'] = (100 * problems_done) / problems_total
        # TODO: Put this somewhere else! What is this on about? Why 16?
        # XXX Marks calculation (should be abstracted out of here!)
        # percent / 16, rounded down, with a maximum mark of 5
        ctx['max_mark'] = 5
        ctx['mark'] = min(problems_pct / 16, max_mark)

def get_worksheets(subjectfile):
    '''Given a subject stream, get all the worksheets and put them in ctx'''
    worksheets = []
    for kind, data, pos in subjectfile:
        if kind is genshi.core.START:
            if data[0] == 'worksheet':
                worksheetid = ''
                worksheetname = ''
                worksheetasses = False
                for attr in data[1]:
                    if attr[0] == 'id':
                        worksheetid = attr[1]
                    elif attr[0] == 'name':
                        worksheetname = attr[1]
                    elif attr[0] == 'assessable':
                        worksheetasses = attr[1] == 'true'
                worksheets.append(Worksheet(worksheetid, worksheetname, \
                                                            worksheetasses))
    return worksheets

def handle_worksheet(req, ctx, subject, worksheet):
    # Subject and worksheet names must be valid identifiers
    if not is_valid_subjname(subject) or not is_valid_subjname(worksheet):
        req.throw_error(req.HTTP_NOT_FOUND,
            "Invalid subject name %s or worksheet name %s."
                % (repr(subject), repr(worksheet)))

    # Read in worksheet data
    worksheetfilename = os.path.join(ivle.conf.subjects_base, subject,
            worksheet + ".xml")
    try:
        worksheetfile = open(worksheetfilename)
        worksheetmtime = os.path.getmtime(worksheetfilename)
    except:
        req.throw_error(req.HTTP_NOT_FOUND,
            "Worksheet file not found.")
    worksheetmtime = datetime.fromtimestamp(worksheetmtime)
    worksheetfile = worksheetfile.read()
    
    ctx['worksheetstream'] = genshi.Stream(list(genshi.XML(worksheetfile)))

    req.write_html_head_foot = True

    ctx['subject'] = subject
    
    #TODO: Replace this with a nice way, possibly a match template
    generate_worksheet_data(ctx, req)
    
    update_db_worksheet(req.store, subject, worksheet, worksheetmtime,
        ctx['exerciselist'])
    
    ctx['worksheetstream'] = add_exercises(ctx['worksheetstream'], ctx, req)

# This generator adds in the exercises as they are required. This is returned    
def add_exercises(stream, ctx, req):
    """A filter adds exercises into the stream."""
    exid = 0
    for kind, data, pos in stream:
        if kind is genshi.core.START:
            if data[0] == 'exercise':
                new_stream = ctx['exercises'][exid]['stream']
                exid += 1
                for item in new_stream:
                    yield item
            else:
                yield kind, data, pos
        else:
            yield kind, data, pos

# This function runs through the worksheet, to get data on the exercises to
# build a Table of Contents, as well as fill in details in ctx
def generate_worksheet_data(ctx, req):
    """Runs through the worksheetstream, generating the exericises"""
    exid = 0
    ctx['exercises'] = []
    ctx['exerciselist'] = []
    for kind, data, pos in ctx['worksheetstream']:
        if kind is genshi.core.START:
            if data[0] == 'exercise':
                exid += 1
                src = ""
                optional = False
                for attr in data[1]:
                    if attr[0] == 'src':
                        src = attr[1]
                    if attr[0] == 'optional':
                        optional = attr[1] == 'true'
                # Each item in toc is of type (name, complete, stream)
                ctx['exercises'].append(present_exercise(req, src, exid))
                ctx['exerciselist'].append((src, optional))
            elif data[0] == 'worksheet':
                ctx['worksheetname'] = 'bob'
                for attr in data[1]:
                    if attr[0] == 'name':
                        ctx['worksheetname'] = attr[1]

def innerXML(elem):
    """Given an element, returns its children as XML strings concatenated
    together."""
    s = ""
    for child in elem.childNodes:
        s += child.toxml()
    return s

def getTextData(element):
    """ Get the text and cdata inside an element
    Leading and trailing whitespace are stripped
    """
    data = ''
    for child in element.childNodes:
        if child.nodeType == child.CDATA_SECTION_NODE:
            data += child.data
        elif child.nodeType == child.TEXT_NODE:
            data += child.data
        elif child.nodeType == child.ELEMENT_NODE:
            data += getTextData(child)

    return data.strip()

#TODO: This needs to be re-written, to stop using minidom, and get the data
# about the worksheet directly from the database
def present_exercise(req, exercisesrc, exerciseid):
    """Open a exercise file, and write out the exercise to the request in HTML.
    exercisesrc: "src" of the exercise file. A path relative to the top-level
        exercises base directory, as configured in conf.
    """
    # Exercise-specific context is used here, as we already have all the data
    # we need
    curctx = genshi.template.Context()
    curctx['filename'] = exercisesrc
    curctx['exerciseid'] = exerciseid

    # Retrieve the exercise details from the database
    exercise = ivle.database.Exercise.get_by_name(req.store, exercisesrc)
    #Open the exercise, and double-check that it exists
    exercisefile = util.open_exercise_file(exercisesrc)
    if exercisefile is None:
        req.throw_error(req.HTTP_EXPECTATION_FAILED, \
                                        "Exercise file could not be opened")
    
    # Read exercise file and present the exercise
    # Note: We do not use the testing framework because it does a lot more
    # work than we need. We just need to get the exercise name and a few other
    # fields from the XML.

    #TODO: Replace calls to minidom with calls to the database directly
    exercisedom = minidom.parse(exercisefile)
    exercisefile.close()
    exercisedom = exercisedom.documentElement
    if exercisedom.tagName != "exercise":
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR,
            "The exercise XML file's top-level element must be <exercise>.")
    curctx['exercisename'] = exercisedom.getAttribute("name")
    
    curctx['rows'] = exercisedom.getAttribute("rows")
    if not curctx['rows']:
        curctx['rows'] = "12"
    # Look for some other fields we need, which are elements:
    # - desc
    # - partial
    curctx['exercisedesc'] = None
    curctx['exercisepartial'] = ""
    for elem in exercisedom.childNodes:
        if elem.nodeType == elem.ELEMENT_NODE:
            if elem.tagName == "desc":
                curctx['exercisedesc'] = genshi.XML(rst(innerXML(elem).strip()))
            if elem.tagName == "partial":
                curctx['exercisepartial'] = getTextData(elem) + '\n'
    curctx['exercisepartial_backup'] = curctx['exercisepartial']

    # If the user has already saved some text for this problem, or submitted
    # an attempt, then use that text instead of the supplied "partial".
    saved_text = ivle.worksheet.get_exercise_stored_text(req.store,
        req.user, exercise)
    # Also get the number of attempts taken and whether this is complete.
    complete, curctx['attempts'] = \
            ivle.worksheet.get_exercise_status(req.store, req.user, exercise)
    if saved_text is not None:
        curctx['exercisepartial'] = saved_text.text
    if complete:
        curctx['complete'] = 'complete'
    else:
        curctx['complete'] = 'incomplete'

    #Save the exercise details to the Table of Contents

    loader = genshi.template.TemplateLoader(".", auto_reload=True)
    tmpl = loader.load(util.make_local_path("apps/tutorial/exercise.html"))
    ex_stream = tmpl.generate(curctx)
    return {'name': curctx['exercisename'], 'complete': curctx['complete'], \
              'stream': ex_stream, 'exid': exerciseid}


def update_db_worksheet(store, subject, worksheetname, file_mtime,
    exercise_list=None, assessable=None):
    """
    Determines if the database is missing this worksheet or out of date,
    and inserts or updates its details about the worksheet.
    file_mtime is a datetime.datetime with the modification time of the XML
    file. The database will not be updated unless worksheetmtime is newer than
    the mtime in the database.
    exercise_list is a list of (filename, optional) pairs as returned by
    present_table_of_contents.
    assessable is boolean.
    exercise_list and assessable are optional, and if omitted, will not change
    the existing data. If the worksheet does not yet exist, and assessable
    is omitted, it defaults to False.
    """
    worksheet = ivle.database.Worksheet.get_by_name(store, subject,
                                                    worksheetname)

    updated_database = False
    if worksheet is None:
        # If assessable is not supplied, default to False.
        if assessable is None:
            assessable = False
        # Create a new Worksheet
        worksheet = ivle.database.Worksheet(subject=unicode(subject),
            name=unicode(worksheetname), assessable=assessable,
            mtime=datetime.now())
        store.add(worksheet)
        updated_database = True
    else:
        if file_mtime > worksheet.mtime:
            # File on disk is newer than database. Need to update.
            worksheet.mtime = datetime.now()
            if exercise_list is not None:
                # exercise_list is supplied, so delete any existing problems
                worksheet.remove_all_exercises(store)
            if assessable is not None:
                worksheet.assessable = assessable
            updated_database = True

    if updated_database and exercise_list is not None:
        # Insert each exercise into the worksheet
        for exercise_name, optional in exercise_list:
            # Get the Exercise from the DB
            exercise = ivle.database.Exercise.get_by_name(store,exercise_name)
            # Create a new binding between the worksheet and the exercise
            worksheetexercise = ivle.database.WorksheetExercise(
                    worksheet=worksheet, exercise=exercise, optional=optional)

    store.commit()
