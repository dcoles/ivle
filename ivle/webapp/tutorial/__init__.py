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

# Author: Matt Giuca, Will Grant

'''Tutorial/worksheet/exercise application.

Displays tutorial content with editable exercises, allowing students to test
and submit their solutions to exercises and have them auto-tested.
'''

import os
import urllib
import re
import mimetypes
from datetime import datetime
from xml.dom import minidom

import genshi

import ivle.util
import ivle.conf
import ivle.database
from ivle.database import Subject, Offering, Semester, Exercise, ExerciseSave
from ivle.database import Worksheet as DBWorksheet
import ivle.worksheet
from ivle.webapp.base.views import BaseView
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.media import BaseMediaFileView
from ivle.webapp.errors import NotFound, Forbidden
from ivle.webapp.tutorial.rst import rst as rstfunc
from ivle.webapp.tutorial.service import AttemptsRESTView, AttemptRESTView, \
                                         ExerciseRESTView, WorksheetRESTView

# Regex for valid identifiers (subject/worksheet names)
re_ident = re.compile("[0-9A-Za-z_]+")

class Worksheet:
    def __init__(self, id, name, assessable):
        self.id = id
        self.name = name
        self.assessable = assessable
        self.complete_class = ''
        self.optional_message = ''
        self.total = 0
        self.mand_done = 0
    def __repr__(self):
        return ("Worksheet(id=%s, name=%s, assessable=%s)"
                % (repr(self.id), repr(self.name), repr(self.assessable)))

class OfferingView(XHTMLView):
    '''The view of the index of worksheets for an offering.'''
    template = 'subjectmenu.html'
    appname = 'tutorial' # XXX
    permission = 'view'

    def __init__(self, req, subject, year, semester):
        self.context = req.store.find(Offering,
            Offering.subject_id == Subject.id,
            Subject.code == subject,
            Offering.semester_id == Semester.id,
            Semester.year == year,
            Semester.semester == semester).one()

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['tutorial.css']

        if not self.context:
            raise NotFound()

        # Subject names must be valid identifiers
        if not is_valid_subjname(self.context.subject.code):
            raise NotFound()

        # Parse the subject description file
        # The subject directory must have a file "subject.xml" in it,
        # or it does not exist (404 error).
        ctx['subject'] = self.context.subject.code
        ctx['year'] = self.context.semester.year
        ctx['semester'] = self.context.semester.semester

        # As we go, calculate the total score for this subject
        # (Assessable worksheets only, mandatory problems only)

        ctx['worksheets'] = []
        problems_done = 0
        problems_total = 0
        for worksheet in self.context.worksheets:
            new_worksheet = Worksheet(worksheet.identifier, worksheet.name, 
                                      worksheet.assessable)
            if new_worksheet.assessable:
                # Calculate the user's score for this worksheet
                mand_done, mand_total, opt_done, opt_total = (
                    ivle.worksheet.calculate_score(req.store, req.user,
                        worksheet))
                if opt_total > 0:
                    optional_message = " (excluding optional exercises)"
                else:
                    optional_message = ""
                if mand_done >= mand_total:
                    new_worksheet.complete_class = "complete"
                elif mand_done > 0:
                    new_worksheet.complete_class = "semicomplete"
                else:
                    new_worksheet.complete_class = "incomplete"
                problems_done += mand_done
                problems_total += mand_total
                new_worksheet.mand_done = mand_done
                new_worksheet.total = mand_total
                new_worksheet.optional_message = optional_message
            ctx['worksheets'].append(new_worksheet)


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
            ctx['mark'] = min(ctx['problems_pct'] / 16, ctx['max_mark'])

class WorksheetView(XHTMLView):
    '''The view of a worksheet with exercises.'''
    template = 'worksheet.html'
    appname = 'tutorial' # XXX
    permission = 'view'

    def __init__(self, req, subject, year, semester, worksheet):
        # XXX: Worksheet is actually context, but it's not really there yet.
        self.context = req.store.find(DBWorksheet,
            DBWorksheet.offering_id == Offering.id,
            Offering.subject_id == Subject.id,
            Subject.code == subject,
            Offering.semester_id == Semester.id,
            Semester.year == year,
            Semester.semester == semester,
            DBWorksheet.identifier == worksheet).one()
        
        self.worksheetname = worksheet
        self.year = year
        self.semester = semester

    def populate(self, req, ctx):
        self.plugin_scripts[Plugin] = ['tutorial.js']
        self.plugin_styles[Plugin] = ['tutorial.css']

        if not self.context:
            raise NotFound()

        ctx['subject'] = self.context.offering.subject.code
        ctx['worksheet'] = self.worksheetname
        ctx['semester'] = self.semester
        ctx['year'] = self.year
        ctx['worksheetstream'] = genshi.Stream(list(genshi.XML(self.context.data)))

        generate_worksheet_data(ctx, req, self.context)

        ctx['worksheetstream'] = add_exercises(ctx['worksheetstream'], ctx, req)

class SubjectMediaView(BaseMediaFileView):
    '''The view of subject media files.

    URIs pointing here will just be served directly, from the subject's
    media directory.
    '''
    permission = 'view'

    def __init__(self, req, subject, path):
        self.context = req.store.find(Subject, code=subject).one()
        self.path = os.path.normpath(path)

    def _make_filename(self, req):
        # If the subject doesn't exist, self.subject will be None. Die.
        if not self.context:
            raise NotFound()

        subjectdir = os.path.join(ivle.conf.subjects_base,
                                  self.context.code, 'media')
        return os.path.join(subjectdir, self.path)

def is_valid_subjname(subject):
    m = re_ident.match(subject)
    return m is not None and m.end() == len(subject)

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

# This generator adds in the exercises as they are required. This is returned    
def add_exercises(stream, ctx, req):
    """A filter which adds exercises into the stream."""
    exid = 0
    for kind, data, pos in stream:
        if kind is genshi.core.START:
            # Remove the worksheet tags, as they are not xhtml valid.
            if data[0] == 'worksheet':
                continue
            # If we have an exercise node, replace it with the content of the
            # exercise.
            elif data[0] == 'exercise':
                new_stream = ctx['exercises'][exid]['stream']
                exid += 1
                for item in new_stream:
                    yield item
            else:
                yield kind, data, pos
        # Remove the end tags for exercises and worksheets
        elif kind is genshi.core.END:
            if data == 'exercise':
                continue
            elif data == 'worksheet':
                continue
            else:
                yield kind, data, pos
        else:
            yield kind, data, pos

# This function runs through the worksheet, to get data on the exercises to
# build a Table of Contents, as well as fill in details in ctx
def generate_worksheet_data(ctx, req, worksheet):
    """Runs through the worksheetstream, generating the exericises"""
    ctx['exercises'] = []
    ctx['exerciselist'] = []
    for kind, data, pos in ctx['worksheetstream']:
        if kind is genshi.core.START:
            if data[0] == 'exercise':
                src = ""
                optional = False
                for attr in data[1]:
                    if attr[0] == 'src':
                        src = attr[1]
                    if attr[0] == 'optional':
                        optional = attr[1] == 'true'
                # Each item in toc is of type (name, complete, stream)
                if src != "":
                    ctx['exercises'].append(present_exercise(req, src, worksheet))
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
def present_exercise(req, exercisesrc, worksheet):
    """Open a exercise file, and write out the exercise to the request in HTML.
    exercisesrc: "src" of the exercise file. A path relative to the top-level
        exercises base directory, as configured in conf.
    """
    # Exercise-specific context is used here, as we already have all the data
    # we need
    curctx = genshi.template.Context()
    curctx['filename'] = exercisesrc

    # Retrieve the exercise details from the database
    exercise = req.store.find(Exercise, Exercise.id == unicode(exercisesrc)).one()
    
    if exercise is None:
        raise NotFound(exercisesrc)

    # Read exercise file and present the exercise
    # Note: We do not use the testing framework because it does a lot more
    # work than we need. We just need to get the exercise name and a few other
    # fields from the XML.

    #TODO: Replace calls to minidom with calls to the database directly
    curctx['exercise'] = exercise
    if exercise.description is not None:
        desc = rstfunc(exercise.description)
        curctx['description'] = genshi.XML('<div id="description">' + desc + 
                                           '</div>')
        #curctx['description'] = genshi.XML('<div id="description">' + 
        #                                   exercise.description + '</div>')
    else:
        curctx['description'] = None

    # If the user has already saved some text for this problem, or submitted
    # an attempt, then use that text instead of the supplied "partial".
    save = req.store.find(ExerciseSave, 
                          ExerciseSave.exercise_id == exercise.id,
                          ExerciseSave.worksheetid == worksheet.id,
                          ExerciseSave.user_id == req.user.id
                          ).one()
    # Also get the number of attempts taken and whether this is complete.
    complete, curctx['attempts'] = \
            ivle.worksheet.get_exercise_status(req.store, req.user, 
                                               exercise, worksheet)
    if save is not None:
        curctx['exercisesave'] = save.text
    else:
        curctx['exercisesave']= exercise.partial
    curctx['complete'] = 'Complete' if complete else 'Incomplete'
    curctx['complete_class'] = curctx['complete'].lower()

    #Save the exercise details to the Table of Contents

    loader = genshi.template.TemplateLoader(".", auto_reload=True)
    tmpl = loader.load(os.path.join(os.path.dirname(__file__), "exercise.html"))
    ex_stream = tmpl.generate(curctx)
    return {'name': exercise.name,
            'complete': curctx['complete_class'],
            'stream': ex_stream,
            'exid': exercise.id}

class OfferingAdminView(XHTMLView):
    """The admin view for an Offering.
    
    This class is designed to check the user has admin privileges, and
    then allow them to edit the RST for the offering, which controls which
    worksheets are actually displayed on the page."""
    pass

class WorksheetAdminView(XHTMLView):
    """The admin view for an offering.
    
    This view is designed to replace worksheets.xml, turning them instead
    into XML directly from RST."""
    permission = "edit"
    template = "worksheet_admin.html"
    appname = "Worksheet Admin"

    def __init__(self, req, subject, year, semester, worksheet):
        self.context = req.store.find(DBWorksheet,
            DBWorksheet.identifier == worksheet,
            DBWorksheet.offering_id == Offering.id,
            Offering.semester_id == Semester.id,
            Semester.year == year,
            Semester.semester == semester,
            Offering.subject_id == Subject.id,
            Subject.code == subject
        ).one()
        
        self.subject = subject
        self.year = year
        self.semester = semester
        self.worksheet = worksheet
        
        if self.context is None:
            raise NotFound()
            
    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ["tutorial_admin.css"]
        self.plugin_scripts[Plugin] = ['tutorial_admin.js']
        
        ctx['worksheet'] = self.context
        ctx['worksheetname'] = self.worksheet
        ctx['subject'] = self.subject
        ctx['year'] = self.year
        ctx['semester'] = self.semester


class Plugin(ViewPlugin, MediaPlugin):
    urls = [
        ('subjects/:subject/:year/:semester/+worksheets', OfferingView),
        ('subjects/:subject/+worksheets/+media/*(path)', SubjectMediaView),
        ('subjects/:subject/:year/:semester/+worksheets/:worksheet', WorksheetView),
        ('subjects/:subject/:year/:semester/+worksheets/:worksheet/+edit', WorksheetAdminView),
        ('api/subjects/:subject/:year/:semester/+worksheets/:worksheet/*exercise/'
            '+attempts/:username', AttemptsRESTView),
        ('api/subjects/:subject/:year/:semester/+worksheets/:worksheet/*exercise/'
                '+attempts/:username/:date', AttemptRESTView),
        ('api/subjects/:subject/:year/:semester/+worksheets/:worksheet', WorksheetRESTView),
        ('api/subjects/:subject/:year/:semester/+worksheets/:worksheet/*exercise', ExerciseRESTView),
    ]

    tabs = [
        ('tutorial', 'Worksheets',
         'Online tutorials and exercises for lab work.', 'tutorial.png',
         'tutorial', 2)
    ]

    media = 'media'
    help = {'Tutorial': 'help.html'}
