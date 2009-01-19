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

THIS_APP = "tutorial"

# Regex for valid identifiers (subject/worksheet names)
re_ident = re.compile("[0-9A-Za-z_]+")

class Worksheet:
    def __init__(self, id, name, assessable):
        self.id = id
        self.name = name
        self.assessable = assessable
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
        handle_toplevel_menu(req)
    elif worksheet == None:
        handle_subject_menu(req, subject)
    else:
        handle_worksheet(req, subject, worksheet)

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

def handle_toplevel_menu(req):
    # This is represented as a directory. Redirect and add a slash if it is
    # missing.
    if req.uri[-1] != '/':
        req.throw_redirect(make_tutorial_path())
    req.write_html_head_foot = True
    req.write('<div id="ivle_padding">\n')
    req.write("<h1>IVLE Tutorials</h1>\n")
    req.write("""<p>Welcome to the IVLE tutorial system.
  Please select a subject from the list below to select a worksheet
  for that subject.</p>\n""")

    enrolled_subjects = req.user.subjects
    unenrolled_subjects = [subject for subject in
                           req.store.find(ivle.database.Subject)
                           if subject not in enrolled_subjects]

    def print_subject(subject):
        req.write('  <li><a href="%s">%s</a></li>\n'
            % (urllib.quote(subject.code) + '/',
               cgi.escape(subject.name)))

    req.write("<h2>Subjects</h2>\n<ul>\n")
    for subject in enrolled_subjects:
        print_subject(subject)
    req.write("</ul>\n")
    if len(unenrolled_subjects) > 0:
        req.write("<h3>Other Subjects</h3>\n")
        req.write("<p>You are not currently enrolled in these subjects.\n"
                  "   Your marks will not be counted.</p>\n")
        req.write("<ul>\n")
        for subject in unenrolled_subjects:
            print_subject(subject)
        req.write("</ul>\n")
    req.write("</div>\n")   # tutorialbody

def is_valid_subjname(subject):
    m = re_ident.match(subject)
    return m is not None and m.end() == len(subject)

def handle_subject_menu(req, subject):
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
    try:
        subjectfile = open(os.path.join(ivle.conf.subjects_base, subject,
            "subject.xml"))
    except:
        req.throw_error(req.HTTP_NOT_FOUND,
            "Subject %s not found." % repr(subject))

    # Read in data about the subject
    subjectdom = minidom.parse(subjectfile)
    subjectfile.close()
    # TEMP: All of this is for a temporary XML format, which will later
    # change.
    worksheetsdom = subjectdom.documentElement
    worksheets = []     # List of string IDs
    for worksheetdom in worksheetsdom.childNodes:
        if worksheetdom.nodeType == worksheetdom.ELEMENT_NODE:
            # Get the 3 attributes for this node and construct a Worksheet
            # object.
            # (Note: assessable will default to False, unless it is explicitly
            # set to "true").
            worksheet = Worksheet(worksheetdom.getAttribute("id"),
                worksheetdom.getAttribute("name"),
                worksheetdom.getAttribute("assessable") == "true")
            worksheets.append(worksheet)

    # Now all the errors are out the way, we can begin writing
    req.title = "Tutorial - %s" % subject
    req.write_html_head_foot = True
    req.write('<div id="ivle_padding">\n')
    req.write("<h1>IVLE Tutorials - %s</h1>\n" % cgi.escape(subject))
    req.write('<h2>Worksheets</h2>\n<ul id="tutorial-toc">\n')
    # As we go, calculate the total score for this subject
    # (Assessable worksheets only, mandatory problems only)
    problems_done = 0
    problems_total = 0
    for worksheet_from_xml in worksheets:
        worksheet = ivle.database.Worksheet.get_by_name(req.store,
            subject, worksheet_from_xml.id)
        # If worksheet is not in database yet, we'll simply not display
        # data about it yet (it should be added as soon as anyone visits
        # the worksheet itself).
        req.write('  <li><a href="%s">%s</a>'
            % (urllib.quote(worksheet_from_xml.id),
                cgi.escape(worksheet_from_xml.name)))
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
                    complete_class = "complete"
                elif mand_done > 0:
                    complete_class = "semicomplete"
                else:
                    complete_class = "incomplete"
                problems_done += mand_done
                problems_total += mand_total
                req.write('\n    <ul><li class="%s">'
                        'Completed %d/%d%s</li></ul>\n  '
                        % (complete_class, mand_done, mand_total,
                            optional_message))
        req.write('</li>\n')
    req.write("</ul>\n")
    if problems_total > 0:
        if problems_done >= problems_total:
            complete_class = "complete"
        elif problems_done > 0:
            complete_class = "semicomplete"
        else:
            complete_class = "incomplete"
        problems_pct = (100 * problems_done) / problems_total       # int
        req.write('<ul><li class="%s">Total exercises completed: %d/%d '
                    '(%d%%)</li></ul>\n'
            % (complete_class, problems_done, problems_total,
                problems_pct))
        # XXX Marks calculation (should be abstracted out of here!)
        # percent / 16, rounded down, with a maximum mark of 5
        max_mark = 5
        mark = min(problems_pct / 16, max_mark)
        req.write('<p style="font-weight: bold">Worksheet mark: %d/%d'
                    '</p>\n' % (mark, max_mark))
    req.write("</div>\n")   # tutorialbody

def handle_worksheet(req, subject, worksheet):
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

    worksheetdom = minidom.parse(worksheetfile)
    worksheetfile.close()
    # TEMP: All of this is for a temporary XML format, which will later
    # change.
    worksheetdom = worksheetdom.documentElement
    if worksheetdom.tagName != "worksheet":
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR,
            "The worksheet XML file's top-level element must be <worksheet>.")
    worksheetname = worksheetdom.getAttribute("name")

    # Now all the errors are out the way, we can begin writing
    req.title = "Tutorial - %s" % worksheetname
    req.write_html_head_foot = True
    req.write('<div id="ivle_padding">\n')
    req.write("<h1>IVLE Tutorials - %s</h1>\n<h2>%s</h2>\n"
        % (cgi.escape(subject), cgi.escape(worksheetname)))
    exercise_list = present_table_of_contents(req, worksheetdom, 0)
    # If the database is missing this worksheet or out of date, update its
    # details about this worksheet
    # Note: Do NOT set assessable (this is done at the subject level).
    update_db_worksheet(req.store, subject, worksheet, worksheetmtime,
        exercise_list)

    # Write each element
    exerciseid = 0
    for node in worksheetdom.childNodes:
        exerciseid = present_worksheet_node(req, node, exerciseid)
    req.write("</div>\n")   # tutorialbody

def present_table_of_contents(req, node, exerciseid):
    """Given a node of a worksheet XML document, writes out a table of
    contents to the request. This recursively searches for "excercise"
    and heading elements to write out.

    When exercise elements are encountered, the DB is queried for their
    completion status, and the ball is shown of the appropriate colour.

    exerciseid is the ID to use for the first exercise.

    As a secondary feature, this records the identifier (xml filename) and
    optionality of each exercise in a list of pairs [(str, bool)], and returns
    this list. This can be used to cache this information in the database.
    """
    exercise_list = []
    # XXX This means the DB is queried twice for each element.
    # Consider caching these results for lookup later.
    req.write("""<div id="tutorial-toc">
<h2>Worksheet Contents</h2>
<ul>
""")
    for tag, xml in find_all_nodes(req, node):
        if tag == "ex":
            # Exercise node
            # Fragment ID is an accumulating exerciseid
            # (The same algorithm is employed when presenting exercises)
            fragment_id = "exercise%d" % exerciseid
            exerciseid += 1
            exercisesrc = xml.getAttribute("src")
            # Optionality: Defaults to False
            exerciseoptional = xml.getAttribute("optional") == "true"
            # Record the name and optionality for returning in the list
            exercise_list.append((exercisesrc, exerciseoptional))
            # TODO: Get proper exercise title
            title = exercisesrc
            # Get the completion status of this exercise
            exercise = ivle.database.Exercise.get_by_name(req.store,
                            exercisesrc)
            complete, _ = ivle.worksheet.get_exercise_status(req.store,
                            req.user, exercise)
            req.write('  <li class="%s" id="toc_li_%s"><a href="#%s">%s'
                '</a></li>\n'
                % ("complete" if complete else "incomplete",
                    fragment_id, fragment_id, cgi.escape(title)))
        else:
            # Heading node
            fragment_id = getID(xml)
            title = getTextData(xml)
            req.write('  <li><a href="#%s">%s</a></li>\n'
                % (fragment_id, cgi.escape(title)))
    req.write('</ul>\n</div>\n')
    return exercise_list

def find_all_nodes(req, node):
    """Generator. Searches through a node and yields all headings and
    exercises. (Recursive).
    When finding a heading, yields a pair ("hx", headingnode), where "hx" is
    the element name, such as "h1", "h2", etc.
    When finding an exercise, yields a pair ("ex", exercisenode), where
    exercisenode is the DOM node for this exercise.
    """
    if node.nodeType == node.ELEMENT_NODE:
        if node.tagName == "exercise":
            yield "ex", node
        elif (node.tagName == "h1" or node.tagName == "h2"
            or node.tagName == "h3"):
            yield node.tagName, node
        else:
            # Some other element. Recurse.
            for childnode in node.childNodes:
                for yieldval in find_all_nodes(req, childnode):
                    yield yieldval

def present_worksheet_node(req, node, exerciseid):
    """Given a node of a worksheet XML document, writes it out to the
    request. This recursively searches for "exercise" elements and handles
    those specially (presenting their XML exercise spec and input box), and
    just dumps the other elements as regular HTML.

    exerciseid is the ID to use for the first exercise.
    Returns the new exerciseid after all the exercises have been written
    (since we need unique IDs for each exercise).
    """
    if node.nodeType == node.ELEMENT_NODE:
        if node.tagName == "exercise":
            present_exercise(req, node.getAttribute("src"), exerciseid)
            exerciseid += 1
        else:
            # Some other element. Write out its head and foot, and recurse.
            req.write("<" + node.tagName)
            # Attributes
            attrs = map(lambda (k,v): '%s="%s"'
                    % (cgi.escape(k), cgi.escape(v)), node.attributes.items())
            if len(attrs) > 0:
                req.write(" " + ' '.join(attrs))
            req.write(">")
            for childnode in node.childNodes:
                exerciseid = present_worksheet_node(req, childnode, exerciseid)
            req.write("</" + node.tagName + ">")
    else:
        # No need to recurse, so just print this node's contents
        req.write(node.toxml())
    return exerciseid

def innerXML(elem):
    """Given an element, returns its children as XML strings concatenated
    together."""
    s = ""
    for child in elem.childNodes:
        s += child.toxml()
    return s

def getID(element):
    """Get the first ID attribute found when traversing a node and its
    children. (This is used to make fragment links to a particular element).
    Returns None if no ID is found.
    """
    id = element.getAttribute("id")
    if id is not None and id != '':
        return id
    for child in element.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            id = getID(child)
            if id is not None:
                return id
    return None

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

def present_exercise(req, exercisesrc, exerciseid):
    """Open a exercise file, and write out the exercise to the request in HTML.
    exercisesrc: "src" of the exercise file. A path relative to the top-level
        exercises base directory, as configured in conf.
    """
    req.write('<div class="exercise" id="exercise%d">\n'
        % exerciseid)
    exercise = ivle.database.Exercise.get_by_name(req.store, exercisesrc)
    exercisefile = util.open_exercise_file(exercisesrc)
    if exercisefile is None:
        req.write("<p><b>Server Error</b>: "
            + "Exercise file could not be opened.</p>\n")
        req.write("</div>\n")
        return
    
    # Read exercise file and present the exercise
    # Note: We do not use the testing framework because it does a lot more
    # work than we need. We just need to get the exercise name and a few other
    # fields from the XML.

    exercisedom = minidom.parse(exercisefile)
    exercisefile.close()
    exercisedom = exercisedom.documentElement
    if exercisedom.tagName != "exercise":
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR,
            "The exercise XML file's top-level element must be <exercise>.")
    exercisename = exercisedom.getAttribute("name")
    rows = exercisedom.getAttribute("rows")
    if not rows:
        rows = "12"
    # Look for some other fields we need, which are elements:
    # - desc
    # - partial
    exercisedesc = None
    exercisepartial= ""
    for elem in exercisedom.childNodes:
        if elem.nodeType == elem.ELEMENT_NODE:
            if elem.tagName == "desc":
                exercisedesc = rst(innerXML(elem).strip())
            if elem.tagName == "partial":
                exercisepartial= getTextData(elem) + '\n'
    exercisepartial_backup = exercisepartial

    # If the user has already saved some text for this problem, or submitted
    # an attempt, then use that text instead of the supplied "partial".
    saved_text = ivle.worksheet.get_exercise_stored_text(req.store,
        req.user, exercise)
    # Also get the number of attempts taken and whether this is complete.
    complete, attempts = ivle.worksheet.get_exercise_status(req.store,
        req.user, exercise)
    if saved_text is not None:
        exercisepartial = saved_text.text

    # Print this exercise out to HTML 
    req.write("<p><b>Exercise:</b> %s</p>\n" % cgi.escape(exercisename))
    if exercisedesc is not None:
        req.write("<div>%s</div>\n" % exercisedesc)
    filename = cgi.escape(cjson.encode(exercisesrc), quote=True)
    req.write("""<input id="input_resettext_exercise%d" type="hidden"
    value="%s" />"""
        % (exerciseid, urllib.quote(exercisepartial_backup)))
    req.write("""<textarea id="textarea_exercise%d" class="exercisebox"
    onkeypress="return catch_textbox_input(&quot;exercise%d&quot;, %s,
        event.keyCode)"
    onchange="set_saved_status(&quot;exercise%d&quot;, %s,
        &quot;Save&quot;)"
    cols="80" rows="%s">%s</textarea>"""
        % (exerciseid, exerciseid, filename, exerciseid, filename,
            rows, cgi.escape(exercisepartial)))
    req.write("""\n<div class="exercisebuttons">\n""")
    req.write("""  <input type="button" value="Saved" disabled="disabled"
    id="savebutton_exercise%d"
    onclick="saveexercise(&quot;exercise%d&quot;, %s)"
    title="Save your solution to this exercise" />\n"""
        % (exerciseid, exerciseid, filename))
    req.write("""  <input type="button" value="Reset"
    id="resetbutton_exercise%d"
    onclick="resetexercise(&quot;exercise%d&quot;, %s)"
    title="Reload the original partial solution for this exercise" />\n"""
        % (exerciseid, exerciseid, filename))
    req.write("""  <input type="button" value="Run"
    onclick="runexercise(&quot;exercise%d&quot;, %s)"
    title="Run this program in the console" />\n"""
        % (exerciseid, filename))
    req.write("""  <input type="button" value="Submit"
    id="submitbutton_exercise%d"
    onclick="submitexercise(&quot;exercise%d&quot;, %s)"
    title="Submit this solution for evaluation" />\n"""
        % (exerciseid, exerciseid, filename))
    req.write("""</div>
<div class="testoutput">
</div>
""")
    # Write the "summary" - whether this problem is complete and how many
    # attempts it has taken.
    req.write("""<div class="problem_summary">
  <ul><li id="summaryli_exercise%d" class="%s">
    <b><span id="summarycomplete_exercise%d">%s</span>.</b>
    Attempts: <span id="summaryattempts_exercise%d">%d</span>.
  </li></ul>
</div>
""" % (exerciseid, "complete" if complete else "incomplete",
        exerciseid, "Complete" if complete else "Incomplete",
        exerciseid, attempts))
    # Write the attempt history infrastructure
    req.write("""<div class="attempthistory">
  <p><a title="Click to view previous submissions you have made for this \
exercise" onclick="open_previous(&quot;exercise%d&quot;, %s)">View previous \
attempts</a></p>
  <div style="display: none">
    <h3>Previous attempts</h3>
    <p><a title="Close the previous attempts" \
onclick="close_previous(&quot;exercise%d&quot;)">Close attempts</a></p>
    <p>
      <select title="Select an attempt's time stamp from the list">
        <option></option>
      </select>
      <input type="button" value="View"
        onclick="select_attempt(&quot;exercise%d&quot;, %s)" />
    </p>
    <p><textarea readonly="readonly" class="exercisebox" cols="80" rows="%s"
        title="You submitted this code on a previous attempt">
       </textarea>
    </p>
  </div>
</div>
""" % (exerciseid, filename, exerciseid, exerciseid, filename, rows))
    req.write("</div>\n")

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
        worksheet = ivle.database.Worksheet(subject=subject,
            name=worksheetname, assessable=assessable, mtime=datetime.now())
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
