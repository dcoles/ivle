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
import cgi
import urllib
import re
from xml.dom import minidom
import mimetypes

import cjson

from common import util
import conf
import plugins.console

from rst import rst

THIS_APP = "tutorial"

# Regex for valid identifiers (subject/worksheet names)
re_ident = re.compile("[0-9A-Za-z_]+")

class Worksheet:
    def __init__(self, id, name):
        self.id = id
        self.name = name
    def __repr__(self):
        return ("Worksheet(id=" + repr(self.id) + ", name=" + repr(self.name)
                + ")")

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
    # Let the console plugin insert its own styles and scripts
    plugins.console.insert_scripts_styles(req.scripts, req.styles)
    # Note: Don't print write_html_head_foot just yet
    # If we encounter errors later we do not want this

    path_segs = req.path.split(os.sep)
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
        plugins.console.present(req, windowpane=True)

def handle_media_path(req):
    """
    Urls in "tutorial/media" will just be served directly, relative to
    subjects. So if we came here, we just want to serve a file relative to the
    subjects directory on the local file system.
    """
    # First normalise the path
    urlpath = os.path.normpath(req.path)
    # Now if it begins with ".." or separator, then it's illegal
    if urlpath.startswith("..") or urlpath.startswith(os.sep):
        req.throw_error(req.HTTP_FORBIDDEN,
            "Invalid path.")
    filename = os.path.join(conf.subjects_base, urlpath)
    (type, _) = mimetypes.guess_type(filename)
    if type is None:
        type = conf.mimetypes.default_mimetype
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
    if req.uri[-1] != os.sep:
        req.throw_redirect(make_tutorial_path())
    req.write_html_head_foot = True
    req.write('<div id="ivle_padding">\n')
    req.write("<h1>IVLE Tutorials</h1>\n")
    req.write("""<p>Welcome to the IVLE tutorial system.
  Please select a subject from the list below to select a worksheet
  for that subject.</p>\n""")
    # Get list of subjects
    # TODO: Fetch from DB. For now, just get directory listing
    subjects = os.listdir(conf.subjects_base)
    subjects.sort()
    req.write("<h2>Subjects</h2>\n<ul>\n")
    for subject in subjects:
        req.write('  <li><a href="%s">%s</a></li>\n'
            % (urllib.quote(subject) + '/', cgi.escape(subject)))
    req.write("</ul>\n")
    req.write("</div>\n")   # tutorialbody

def is_valid_subjname(subject):
    m = re_ident.match(subject)
    return m is not None and m.end() == len(subject)

def handle_subject_menu(req, subject):
    # This is represented as a directory. Redirect and add a slash if it is
    # missing.
    if req.uri[-1] != os.sep:
        req.throw_redirect(make_tutorial_path(subject))
    # Subject names must be valid identifiers
    if not is_valid_subjname(subject):
        req.throw_error(req.HTTP_NOT_FOUND,
            "Invalid subject name: %s." % repr(subject))
    # Parse the subject description file
    # The subject directory must have a file "subject.xml" in it,
    # or it does not exist (404 error).
    try:
        subjectfile = open(os.path.join(conf.subjects_base, subject,
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
            worksheet = Worksheet(worksheetdom.getAttribute("id"),
                worksheetdom.getAttribute("name"))
            worksheets.append(worksheet)

    # Now all the errors are out the way, we can begin writing
    req.title = "Tutorial - %s" % subject
    req.write_html_head_foot = True
    req.write('<div id="ivle_padding">\n')
    req.write("<h1>IVLE Tutorials - %s</h1>\n" % cgi.escape(subject))
    req.write("<h2>Worksheets</h2>\n<ul>\n")
    for worksheet in worksheets:
        req.write('  <li><a href="%s">%s</a></li>\n'
            % (urllib.quote(worksheet.id), cgi.escape(worksheet.name)))
    req.write("</ul>\n")
    req.write("</div>\n")   # tutorialbody

def handle_worksheet(req, subject, worksheet):
    # Subject and worksheet names must be valid identifiers
    if not is_valid_subjname(subject) or not is_valid_subjname(worksheet):
        req.throw_error(req.HTTP_NOT_FOUND,
            "Invalid subject name %s or worksheet name %s."
                % (repr(subject), repr(worksheet)))

    # Read in worksheet data
    try:
        worksheetfile = open(os.path.join(conf.subjects_base, subject,
            worksheet + ".xml"))
    except:
        req.throw_error(req.HTTP_NOT_FOUND,
            "Worksheet file not found.")

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

    # Write each element
    exerciseid = 0
    for node in worksheetdom.childNodes:
        exerciseid = present_worksheet_node(req, node, exerciseid)
    req.write("</div>\n")   # tutorialbody

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

def getTextData(element):
    """ Get the text and cdata inside an element
    Leading and trailing whitespace are stripped
    """
    data = ''
    for child in element.childNodes:
        if child.nodeType == child.CDATA_SECTION_NODE:
            data += child.data
        if child.nodeType == child.TEXT_NODE:
            data += child.data

    return data.strip()

def present_exercise(req, exercisesrc, exerciseid):
    """Open a exercise file, and write out the exercise to the request in HTML.
    exercisesrc: "src" of the exercise file. A path relative to the top-level
        exercises base directory, as configured in conf.
    """
    req.write('<div class="exercise" id="exercise%d">\n'
        % exerciseid)
    # First normalise the path
    exercisesrc = os.path.normpath(exercisesrc)
    # Now if it begins with ".." or separator, then it's illegal
    if exercisesrc.startswith("..") or exercisesrc.startswith(os.sep):
        exercisefile = None
    else:
        exercisefile = os.path.join(conf.exercises_base, exercisesrc)

    try:
        exercisefile = open(exercisefile)
    except (TypeError, IOError):    # TypeError if exercisefile == None
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

    # Print this exercise out to HTML 
    req.write("<p><b>Exercise:</b> %s</p>\n" % exercisename)
    if exercisedesc is not None:
        req.write("<div>%s</div>\n" % exercisedesc)
    req.write('<textarea class="exercisebox" cols="80" rows="%s">%s</textarea>'
            % (rows, exercisepartial))
    filename = cgi.escape(cjson.encode(exercisesrc), quote=True)
    req.write("""\n<div class="exercisebuttons">
  <input type="button" value="Run"
    onclick="runexercise(&quot;exercise%d&quot;, %s)" />
  <input type="button" value="Submit"
    onclick="submitexercise(&quot;exercise%d&quot;, %s)" />
</div>
<div class="testoutput">
</div>
""" % (exerciseid, filename, exerciseid, filename))
    req.write("</div>\n")
