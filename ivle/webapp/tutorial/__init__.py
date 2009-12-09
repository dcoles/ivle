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

import formencode
import formencode.validators
import genshi
from genshi.filters import HTMLFormFiller

import ivle.database
from ivle.database import Subject, Offering, Semester, Exercise, \
                          ExerciseSave, WorksheetExercise, ExerciseAttempt
from ivle.database import Worksheet as DBWorksheet
import ivle.worksheet.utils
from ivle.webapp import ApplicationRoot
from ivle.webapp.base.views import BaseView
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.media import media_url
from ivle.webapp.errors import NotFound
from ivle.worksheet.rst import rst as rstfunc

from ivle.webapp.tutorial.service import (AttemptsRESTView, AttemptRESTView,
            WorksheetExerciseRESTView, WorksheetRESTView, WorksheetsRESTView)
from ivle.webapp.tutorial.exercise_service import ExercisesRESTView, \
                                                  ExerciseRESTView
from ivle.webapp.tutorial.publishing import (root_to_exercise, exercise_url,
            offering_to_worksheet, worksheet_url,
            worksheet_to_worksheetexercise, worksheetexercise_url,
            ExerciseAttempts, worksheetexercise_to_exerciseattempts,
            exerciseattempts_url, exerciseattempts_to_attempt,
            exerciseattempt_url)
from ivle.webapp.tutorial.breadcrumbs import (ExerciseBreadcrumb,
            WorksheetBreadcrumb)
from ivle.webapp.tutorial.media import (SubjectMediaFile, SubjectMediaView,
    subject_to_media)

class Worksheet:
    """This class represents a worksheet and a particular students progress
    through it.
    
    Do not confuse this with a worksheet in the database. This worksheet
    has extra information for use in the output, such as marks."""
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
    template = 'templates/subjectmenu.html'
    tab = 'subjects' # XXX
    permission = 'view'
    breadcrumb_text = 'Worksheets'

    def populate(self, req, ctx):
        """Create the context for the given offering."""
        self.plugin_styles[Plugin] = ['tutorial.css']

        ctx['subject'] = self.context.subject
        ctx['offering'] = self.context
        ctx['user'] = req.user

        # As we go, calculate the total score for this subject
        # (Assessable worksheets only, mandatory problems only)

        ctx['worksheets'] = []
        problems_done = 0
        problems_total = 0
        # Offering.worksheets is ordered by the worksheets seq_no
        for worksheet in self.context.worksheets:
            new_worksheet = Worksheet(worksheet.identifier, worksheet.name, 
                                      worksheet.assessable)
            if new_worksheet.assessable:
                # Calculate the user's score for this worksheet
                mand_done, mand_total, opt_done, opt_total = (
                    ivle.worksheet.utils.calculate_score(req.store, req.user,
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
            # Calculate the final percentage and mark for the subject
            ctx['problems_pct'], ctx['mark'], ctx['max_mark'] = (
                ivle.worksheet.utils.calculate_mark(
                    problems_done, problems_total))

class WorksheetView(XHTMLView):
    '''The view of a worksheet with exercises.'''
    template = 'templates/worksheet.html'
    tab = 'subjects'
    permission = 'view'

    def populate(self, req, ctx):
        self.plugin_scripts[Plugin] = ['tutorial.js']
        self.plugin_styles[Plugin] = ['tutorial.css', 'worksheet.css']

        if not self.context:
            raise NotFound()

        ctx['subject'] = self.context.offering.subject
        ctx['worksheet'] = self.context
        ctx['semester'] = self.context.offering.semester.semester
        ctx['year'] = self.context.offering.semester.year

        ctx['worksheetstream'] = genshi.Stream(list(genshi.XML(self.context.get_xml())))
        ctx['user'] = req.user

        generate_worksheet_data(ctx, req, self.context)

        ctx['worksheetstream'] = add_exercises(ctx['worksheetstream'], ctx, req)

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

# This generator adds in the exercises as they are required. This is returned.
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
                # XXX: Note that we presume ctx['exercises'] has a correct list
                #      of exercises. If it doesn't, something has gone wrong.
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

def present_exercise(req, src, worksheet):
    """Open a exercise file, and write out the exercise to the request in HTML.
    exercisesrc: "src" of the exercise file. A path relative to the top-level
        exercises base directory, as configured in conf.
    """
    # Exercise-specific context is used here, as we already have all the data
    # we need
    curctx = genshi.template.Context()

    worksheet_exercise = req.store.find(WorksheetExercise,
        WorksheetExercise.worksheet_id == worksheet.id,
        WorksheetExercise.exercise_id == src).one()

    if worksheet_exercise is None:
        raise NotFound()

    # Retrieve the exercise details from the database
    exercise = req.store.find(Exercise, 
        Exercise.id == worksheet_exercise.exercise_id).one()

    if exercise is None:
        raise NotFound(exercisesrc)

    # Read exercise file and present the exercise
    # Note: We do not use the testing framework because it does a lot more
    # work than we need. We just need to get the exercise name and a few other
    # fields from the XML.

    curctx['exercise'] = exercise
    if exercise.description is not None:
        desc = rstfunc(exercise.description)
        curctx['description'] = genshi.XML('<div id="description">' + desc + 
                                           '</div>')
    else:
        curctx['description'] = None

    # If the user has already saved some text for this problem, or submitted
    # an attempt, then use that text instead of the supplied "partial".
    # Get exercise stored text will return a save, or the most recent attempt,
    # whichever is more recent
    save = ivle.worksheet.utils.get_exercise_stored_text(
                        req.store, req.user, worksheet_exercise)

    # Also get the number of attempts taken and whether this is complete.
    complete, curctx['attempts'] = \
            ivle.worksheet.utils.get_exercise_status(req.store, req.user, 
                                               worksheet_exercise)
    if save is not None:
        curctx['exercisesave'] = save.text
    else:
        curctx['exercisesave']= exercise.partial
    curctx['complete'] = 'Complete' if complete else 'Incomplete'
    curctx['complete_class'] = curctx['complete'].lower()

    #Save the exercise details to the Table of Contents

    loader = genshi.template.TemplateLoader(".", auto_reload=True)
    tmpl = loader.load(os.path.join(os.path.dirname(__file__),
        "templates/exercise.html"))
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

class WorksheetEditView(XHTMLView):
    """The admin view for an offering.
    
    This view is designed to replace worksheets.xml, turning them instead
    into XML directly from RST."""
    permission = "edit"
    template = "templates/worksheet_edit.html"
    tab = "subjects"

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ["tutorial_admin.css"]
        self.plugin_scripts[Plugin] = ['tutorial_admin.js']

        ctx['worksheet'] = self.context
        ctx['worksheetname'] = self.context.identifier
        ctx['subject'] = self.context.offering.subject
        ctx['year'] = self.context.offering.semester.year
        ctx['semester'] = self.context.offering.semester.semester
        #XXX: Get the list of formats from somewhere else
        ctx['formats'] = ['xml', 'rst']


WORKSHEET_FORMATS = {'XML': 'xml', 'reStructuredText': 'rst'}

class WorksheetFormatValidator(formencode.FancyValidator):
    """A FormEncode validator that turns a username into a user.

    The state must have a 'store' attribute, which is the Storm store
    to use."""
    def _to_python(self, value, state):
        if value not in WORKSHEET_FORMATS.values():
            raise formencode.Invalid('Unsupported format', value, state)
        return value


class WorksheetIdentifierUniquenessValidator(formencode.FancyValidator):
    """A FormEncode validator that checks that a worksheet name is unused.

    If initialised with a 'matching' argument, that worksheet is permitted
    to hold that name. If any other object holds it, the input is rejected.

    The state must have an 'offering' attribute.
    """
    def __init__(self, matching=None):
        self.matching = matching

    def _to_python(self, value, state):
        if (state.store.find(
            DBWorksheet, offering=state.offering,
            identifier=value).one() not in (None, self.matching)):
            raise formencode.Invalid(
                'Short name already taken', value, state)
        return value


class WorksheetSchema(formencode.Schema):
    identifier = formencode.validators.UnicodeString(not_empty=True)
    name = formencode.validators.UnicodeString(not_empty=True)
    assessable = formencode.validators.StringBoolean(if_missing=False)
    data = formencode.validators.UnicodeString(not_empty=True)
    format = formencode.All(
        WorksheetFormatValidator(),
        formencode.validators.UnicodeString(not_empty=True))


class WorksheetAddSchema(WorksheetSchema):
    identifier = formencode.All(
        WorksheetIdentifierUniquenessValidator(),
        formencode.validators.UnicodeString(not_empty=True))


class WorksheetAddView(XHTMLView):
    """A form to add a worksheet to an offering."""
    template = 'templates/worksheet_add.html'
    permission = 'edit'

    def filter(self, stream, ctx):
        return stream | HTMLFormFiller(data=ctx['data'])

    def populate(self, req, ctx):
        if req.method == 'POST':
            data = dict(req.get_fieldstorage())
            try:
                validator = WorksheetAddSchema()
                req.offering = self.context # XXX: Getting into state.
                data = validator.to_python(data, state=req)

                new_worksheet = DBWorksheet()
                new_worksheet.seq_no = self.context.worksheets.count()
                # Setting new_worksheet.offering implicitly adds new_worksheet,
                # hence worksheets.count MUST be called above it
                new_worksheet.offering = self.context
                new_worksheet.identifier = data['identifier']
                new_worksheet.name = data['name']
                new_worksheet.assessable = data['assessable']
                new_worksheet.data = data['data']
                new_worksheet.format = data['format']

                req.store.add(new_worksheet)

                ivle.worksheet.utils.update_exerciselist(new_worksheet)

                req.store.commit()
                req.throw_redirect(req.publisher.generate(new_worksheet))
            except formencode.Invalid, e:
                errors = e.unpack_errors()
        else:
            data = {}
            errors = {}

        ctx['data'] = data or {}
        ctx['offering'] = self.context
        ctx['errors'] = errors
        ctx['formats'] = WORKSHEET_FORMATS

class WorksheetsEditView(XHTMLView):
    """View for arranging worksheets."""
    
    permission = 'edit'
    template = 'templates/worksheets_edit.html'

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['tutorial_admin.css']
        self.plugin_scripts[Plugin] = ['tutorial_admin.js']
        
        ctx['subject'] = self.context.subject
        ctx['year'] = self.context.semester.year
        ctx['semester'] = self.context.semester.semester
        
        ctx['worksheets'] = self.context.worksheets
        
        ctx['mediapath'] = media_url(req, Plugin, 'images/')


class ExerciseEditView(XHTMLView):
    """View for editing a worksheet."""
    
    permission = 'edit'
    template = 'templates/exercise_edit.html'
    
    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['exercise_admin.css']
        self.plugin_scripts[Plugin] = ['exercise_admin.js']
            
        ctx['mediapath'] = media_url(req, Plugin, 'images/')
        
        ctx['exercise'] = self.context
        #XXX: These should come from somewhere else

        ctx['var_types'] = (u'file', u'var', u'arg', u'exception')
        ctx['part_types'] = (u'stdout',u'stderr', u'result',
                             u'exception', u'file', u'code')
        
        ctx['test_types'] = ('norm', 'check')

class ExerciseDeleteView(XHTMLView):
    """View for confirming the deletion of an exercise."""
    
    permission = 'edit'
    template = 'templates/exercise_delete.html'
    
    def populate(self, req, ctx):

        # If post, delete the exercise, or display a message explaining that
        # the exercise cannot be deleted
        if req.method == 'POST':
            ctx['method'] = 'POST'
            try:
                self.context.delete()
                ctx['deleted'] = True
            except:
                ctx['deleted'] = False

        # If get, display a delete confirmation page
        else:
            ctx['method'] = 'GET'
            if self.context.worksheet_exercises.count() is not 0:
                ctx['has_worksheets'] = True
            else:
                ctx['has_worksheets'] = False
        # Variables for the template
        ctx['exercise'] = self.context
        ctx['path'] = "/+exercises/" + self.context.id + "/+delete"

class ExerciseAddView(XHTMLView):
    """View for creating a new exercise."""
    
    permission = 'edit'
    template = 'templates/exercise_add.html'
    #XXX: This should be done somewhere else
    def authorize(self, req):
        for offering in req.store.find(Offering):
            if 'edit' in offering.get_permissions(req.user):
                return True
        return False
        
    def populate(self, req, ctx):
        self.plugin_scripts[Plugin] = ['exercise_admin.js']


class ExercisesView(XHTMLView):
    """View for seeing the list of all exercises"""
    
    permission = 'edit'
    template = 'templates/exercises.html'
    #XXX: This should be done somewhere else
    def authorize(self, req):
        for offering in req.store.find(Offering):
            if 'edit' in offering.get_permissions(req.user):
                return True
        return False
    
    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['exercise_admin.css']
        ctx['exercises'] = req.store.find(Exercise).order_by(Exercise.id)
        ctx['mediapath'] = media_url(req, Plugin, 'images/')


class Plugin(ViewPlugin, MediaPlugin):
    forward_routes = (root_to_exercise, offering_to_worksheet,
        worksheet_to_worksheetexercise, worksheetexercise_to_exerciseattempts,
        exerciseattempts_to_attempt, subject_to_media)

    reverse_routes = (exercise_url, worksheet_url, worksheetexercise_url,
        exerciseattempts_url, exerciseattempt_url)

    breadcrumbs = {Exercise: ExerciseBreadcrumb,
                   DBWorksheet: WorksheetBreadcrumb
                  }

    views = [(Offering, ('+worksheets', '+index'), OfferingView),
             (Offering, ('+worksheets', '+new'), WorksheetAddView),
             (Offering, ('+worksheets', '+edit'), WorksheetsEditView),
             (DBWorksheet, '+index', WorksheetView),
             (DBWorksheet, '+edit', WorksheetEditView),
             (ApplicationRoot, ('+exercises', '+index'), ExercisesView),
             (ApplicationRoot, ('+exercises', '+add'), ExerciseAddView),
             (Exercise, '+edit', ExerciseEditView),
             (Exercise, '+delete', ExerciseDeleteView),
             (SubjectMediaFile, '+index', SubjectMediaView),

             (Offering, ('+worksheets', '+index'), WorksheetsRESTView, 'api'),
             (DBWorksheet, '+index', WorksheetRESTView, 'api'),
             (WorksheetExercise, '+index', WorksheetExerciseRESTView, 'api'),
             (ExerciseAttempts, '+index', AttemptsRESTView, 'api'),
             (ExerciseAttempt, '+index', AttemptRESTView, 'api'),
             (ApplicationRoot, ('+exercises', '+index'), ExercisesRESTView,
              'api'),
             (Exercise, '+index', ExerciseRESTView, 'api'),
             ]

    media = 'media'
    help = {'Tutorial': 'help.html'}
