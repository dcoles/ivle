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
# Displays tutorial content with editable problems, allowing students to test
# and submit their solutions to problems and have them auto-tested.

# URL syntax
# All path segments are optional (omitted path segments will show menus).
# The first path segment is the subject code.
# The second path segment is the worksheet name.

import os
import cgi
import urllib
import re
from xml.dom import minidom

from common import util
import conf

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
    req.styles = [
        "media/tutorial/tutorial.css",
    ]
    # Note: Don't print write_html_head_foot just yet
    # If we encounter errors later we do not want this

    path_segs = req.path.split(os.sep)
    subject = None
    worksheet = None
    if len(path_segs) > 2:
        req.throw_error(req.HTTP_NOT_FOUND)
    elif len(req.path) > 0:
        subject = path_segs[0]
        if len(path_segs) == 2:
            worksheet = path_segs[1]

    if subject == None:
        handle_toplevel_menu(req)
    elif worksheet == None:
        handle_subject_menu(req, subject)
    else:
        handle_worksheet(req, subject, worksheet)

def handle_toplevel_menu(req):
    # This is represented as a directory. Redirect and add a slash if it is
    # missing.
    if req.uri[-1] != os.sep:
        req.throw_redirect(make_tutorial_path())
    req.write_html_head_foot = True
    req.write("<h1>IVLE Tutorials</h1>\n")
    req.write("""<p>Welcome to the IVLE tutorial system.
  Please select a subject from the list below to take a tutorial problem sheet
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
        req.throw_error(req.HTTP_NOT_FOUND)
    # Parse the subject description file
    # The subject directory must have a file "subject.xml" in it,
    # or it does not exist (404 error).
    try:
        subjectfile = open(os.path.join(conf.subjects_base, subject,
            "subject.xml"))
    except:
        req.throw_error(req.HTTP_NOT_FOUND)

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
    req.write_html_head_foot = True
    req.write("<h1>IVLE Tutorials - %s</h1>\n" % cgi.escape(subject))
    req.write("<h2>Worksheets</h2>\n<ul>\n")
    for worksheet in worksheets:
        req.write('  <li><a href="%s">%s</a></li>\n'
            % (urllib.quote(worksheet.id), cgi.escape(worksheet.name)))
    req.write("</ul>\n")

def handle_worksheet(req, subject, worksheet):
    # Subject and worksheet names must be valid identifiers
    if not is_valid_subjname(subject) or not is_valid_subjname(worksheet):
        req.throw_error(req.HTTP_NOT_FOUND)

    # Read in worksheet data
    try:
        worksheetfile = open(os.path.join(conf.subjects_base, subject,
            worksheet + ".xml"))
    except:
        req.throw_error(req.HTTP_NOT_FOUND)

    worksheetdom = minidom.parse(worksheetfile)
    worksheetfile.close()
    # TEMP: All of this is for a temporary XML format, which will later
    # change.
    worksheetdom = worksheetdom.documentElement
    if worksheetdom.tagName != "worksheet":
        # TODO: Nicer error message, to help authors
        req.throw_error(req.HTTP_INTERNAL_SERVER_ERROR)
    worksheetname = worksheetdom.getAttribute("name")
    elements = []     # List of DOM elements
    for elem in worksheetdom.childNodes:
        if elem.nodeType == elem.ELEMENT_NODE:
            elements.append(elem)

    # Now all the errors are out the way, we can begin writing
    req.write_html_head_foot = True
    req.write("<h1>IVLE Tutorials - %s</h1>\n<h2>%s</h2>\n"
        % (cgi.escape(subject), cgi.escape(worksheetname)))
    # Write each element
    for elem in elements:
        if elem.tagName == "problem":
            present_problem(req, subject, elem.getAttribute("src"))
        else:
            # Just treat this as a normal HTML element
            req.write(elem.toxml() + '\n')

def present_problem(req, subject, problemsrc):
    """Open a problem file, and write out the problem to the request in HTML.
    subject: Subject name.
    problemfile: "src" of the problem file. A path relative to the subject
        directory.
    """
    req.write('<div class="tuteproblem">\n')
    # First normalise the path
    problemsrc = os.path.normpath(problemsrc)
    # Now if it begins with ".." or separator, then it's illegal
    if problemsrc.startswith("..") or problemsrc.startswith(os.sep):
        problemfile = None
    else:
        problemfile = os.path.join(conf.subjects_base, subject,
            problemsrc)

    try:
        problemfile = open(problemfile)
    except (TypeError, IOError):    # TypeError if problemfile == None
        req.write("<p><b>Server Error</b>: "
            + "Problem file could not be opened.</p>\n")
        req.write("</div>\n")
        return
    
    # TODO: Read problem file and present the problem
    # TEMP: Print out the problem XML source
    req.write("<p><b>Problem:</b></p>\n")
    req.write("<pre>%s</pre>\n" % cgi.escape(problemfile.read()))
    req.write("</div>\n")
