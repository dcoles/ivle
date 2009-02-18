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
from ivle.webapp.tutorial.service import AttemptsRESTView, \
                                        AttemptRESTView, ExerciseRESTView

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
        try:
            subjectfile = open(os.path.join(ivle.conf.subjects_base,
                                    self.context.subject.code, "subject.xml")).read()
        except:
            raise NotFound()

        subjectfile = genshi.Stream(list(genshi.XML(subjectfile)))

        ctx['worksheets'] = get_worksheets(subjectfile)

        # As we go, calculate the total score for this subject
        # (Assessable worksheets only, mandatory problems only)
        problems_done = 0
        problems_total = 0
        for worksheet in ctx['worksheets']:
            stored_worksheet = req.store.find(DBWorksheet,
                DBWorksheet.offering_id == self.context.id,
                DBWorksheet.name == worksheet.id).one()
            # If worksheet is not in database yet, we'll simply not display
            # data about it yet (it should be added as soon as anyone visits
            # the worksheet itself).
            if stored_worksheet is not None:
                # If the assessable status of this worksheet has changed,
                # update the DB
                # (Note: This fails the try block if the worksheet is not yet
                # in the DB, which is fine. The author should visit the
                # worksheet page to get it into the DB).
                if worksheet.assessable != stored_worksheet.assessable:
                    # XXX If statement to avoid unnecessary database writes.
                    # Is this necessary, or will Storm check for us?
                    stored_worksheet.assessable = worksheet.assessable
                if worksheet.assessable:
                    # Calculate the user's score for this worksheet
                    mand_done, mand_total, opt_done, opt_total = (
                        ivle.worksheet.calculate_score(req.store, req.user,
                            stored_worksheet))
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
            DBWorksheet.name == worksheet).one()
        
        self.worksheetname = worksheet
        self.year = year
        self.semester = semester

    def populate(self, req, ctx):
        self.plugin_scripts[Plugin] = ['tutorial.js']
        self.plugin_styles[Plugin] = ['tutorial.css']

        if not self.context:
            raise NotFound()

        # Read in worksheet data
        worksheetfilename = os.path.join(ivle.conf.subjects_base,
                               self.context.offering.subject.code, self.worksheetname + ".xml")
        try:
            worksheetfile = open(worksheetfilename)
            worksheetmtime = os.path.getmtime(worksheetfilename)
        except:
            raise NotFound()

        worksheetmtime = datetime.fromtimestamp(worksheetmtime)
        worksheetfile = worksheetfile.read()

        ctx['subject'] = self.context.offering.subject.code
        ctx['worksheet'] = self.worksheetname
        ctx['semester'] = self.semester
        ctx['year'] = self.year
        ctx['worksheetstream'] = genshi.Stream(list(genshi.XML(worksheetfile)))

        generate_worksheet_data(ctx, req, self.context)

        update_db_worksheet(req.store, self.context.offering.subject.code, self.worksheetname,
            worksheetmtime, ctx['exerciselist'])

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
    exercise = req.store.find(Exercise, Exercise.id == exercisesrc).one()
    
    if exercise is None:
        raise NotFound()

    # Read exercise file and present the exercise
    # Note: We do not use the testing framework because it does a lot more
    # work than we need. We just need to get the exercise name and a few other
    # fields from the XML.

    #TODO: Replace calls to minidom with calls to the database directly
    curctx['exercise'] = exercise
    if exercise.description is not None:
        curctx['description'] = genshi.XML('<div id="description">' + 
                                           exercise.description + '</div>')
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
"""    worksheet = ivle.database.Worksheet.get_by_name(store, subject,
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
            exercise = store.find(Exercise, Exercise.id == exercise_name).one()
            # Create a new binding between the worksheet and the exercise
            worksheetexercise = ivle.database.WorksheetExercise(
                    worksheet=worksheet, exercise=exercise, optional=optional)

    store.commit()"""

class Plugin(ViewPlugin, MediaPlugin):
    urls = [
        ('subjects/:subject/:year/:semester/+worksheets', OfferingView),
        ('subjects/:subject/+worksheets/+media/*(path)', SubjectMediaView),
        ('subjects/:subject/:year/:semester/+worksheets/:worksheet', WorksheetView),
        ('api/subjects/:subject/:year/:semester/+worksheets/:worksheet/*exercise/'
            '+attempts/:username', AttemptsRESTView),
        ('api/subjects/:subject/:year/:semester/+worksheets/:worksheet/*exercise/'
                '+attempts/:username/:date', AttemptRESTView),
        ('api/subjects/:subject/:year/:semester/+worksheets/:worksheet/*exercise', ExerciseRESTView),
    ]

    tabs = [
        ('tutorial', 'Worksheets',
         'Online tutorials and exercises for lab work.', 'tutorial.png',
         'tutorial', 2)
    ]

    media = 'media'
    help = {'Tutorial': 'help.html'}
