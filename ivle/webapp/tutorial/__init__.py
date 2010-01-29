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
import genshi.input
from genshi.filters import HTMLFormFiller

import ivle.database
from ivle.database import Subject, Offering, Semester, Exercise, \
                          ExerciseSave, WorksheetExercise, ExerciseAttempt
from ivle.database import Worksheet
import ivle.worksheet.utils
from ivle.webapp import ApplicationRoot
from ivle.webapp.base.views import BaseView
from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.base.plugins import ViewPlugin, MediaPlugin
from ivle.webapp.media import media_url
from ivle.webapp.errors import NotFound
from ivle.worksheet.rst import rst as rstfunc

from ivle.webapp.tutorial.service import (AttemptsRESTView, AttemptRESTView,
            WorksheetExerciseRESTView, WorksheetsRESTView)
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
            # exercise. Note that we only consider exercises with a
            # 'src' attribute, the same condition that generate_worksheet_data
            # uses to create ctx['exercises'].
            elif data[0] == 'exercise' and 'src' in dict(data[1]):
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

def present_exercise(req, identifier, worksheet=None):
    """Render an HTML representation of an exercise.

    identifier: The exercise identifier (URL name).
    worksheet: An optional worksheet from which to retrieve saved results.
               If omitted, a clean exercise will be presented.
    """
    # Exercise-specific context is used here, as we already have all the data
    # we need
    curctx = genshi.template.Context()
    curctx['worksheet'] = worksheet

    if worksheet is not None:
        worksheet_exercise = req.store.find(WorksheetExercise,
            WorksheetExercise.worksheet_id == worksheet.id,
            WorksheetExercise.exercise_id == identifier).one()

        if worksheet_exercise is None:
            raise NotFound()

    # Retrieve the exercise details from the database
    exercise = req.store.find(Exercise, 
        Exercise.id == identifier).one()

    if exercise is None:
        raise ExerciseNotFound(identifier)

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
    if worksheet is not None:
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
    else:
        curctx['exercisesave'] = exercise.partial
        curctx['complete'] = 'Incomplete'
        curctx['complete_class'] = curctx['complete'].lower()
        curctx['attempts'] = 0

    #Save the exercise details to the Table of Contents

    loader = genshi.template.TemplateLoader(".", auto_reload=True)
    tmpl = loader.load(os.path.join(os.path.dirname(__file__),
        "templates/exercise_fragment.html"))
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

    The worksheet referenced by state.existing_worksheet is permitted
    to hold that name. If any other object holds it, the input is rejected.

    The state must have an 'offering' attribute.
    """
    def __init__(self, matching=None):
        self.matching = matching

    def _to_python(self, value, state):
        if (state.store.find(
            Worksheet, offering=state.offering,
            identifier=value).one() not in (None, state.existing_worksheet)):
            raise formencode.Invalid(
                'Short name already taken', value, state)
        return value


class WorksheetSchema(formencode.Schema):
    identifier = formencode.All(
        WorksheetIdentifierUniquenessValidator(),
        formencode.validators.UnicodeString(not_empty=True))
    name = formencode.validators.UnicodeString(not_empty=True)
    assessable = formencode.validators.StringBoolean(if_missing=False)
    data = formencode.validators.UnicodeString(not_empty=True)
    format = formencode.All(
        WorksheetFormatValidator(),
        formencode.validators.UnicodeString(not_empty=True))


class WorksheetFormView(XHTMLView):
    """An abstract form for a worksheet in an offering."""

    def filter(self, stream, ctx):
        return stream | HTMLFormFiller(data=ctx['data'])

    def populate_state(self, state):
        state.existing_worksheet = None

    def populate(self, req, ctx):
        if req.method == 'POST':
            data = dict(req.get_fieldstorage())
            try:
                validator = WorksheetSchema()
                req.offering = self.offering # XXX: Getting into state.
                self.populate_state(req)
                data = validator.to_python(data, state=req)

                worksheet = self.get_worksheet_object(req, data)
                ivle.worksheet.utils.update_exerciselist(worksheet)

                req.store.commit()
                req.throw_redirect(req.publisher.generate(worksheet))
            except formencode.Invalid, e:
                errors = e.unpack_errors()
            except genshi.input.ParseError, e:
                errors = {'data': 'Could not parse XML: %s' % e.message}
            except ivle.worksheet.utils.ExerciseNotFound, e:
                errors = {'data': 'Could not find exercise "%s"' % e.message}
        else:
            data = self.get_default_data(req)
            errors = {}

        if errors:
            req.store.rollback()

        ctx['data'] = data or {}
        ctx['offering'] = self.context
        ctx['errors'] = errors
        ctx['formats'] = WORKSHEET_FORMATS


class WorksheetAddView(WorksheetFormView):
    """An form to create a worksheet in an offering."""
    template = 'templates/worksheet_add.html'
    permission = 'edit'

    @property
    def offering(self):
        return self.context

    def get_default_data(self, req):
        return {}

    def get_worksheet_object(self, req, data):
        new_worksheet = Worksheet()
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
        return new_worksheet


class WorksheetEditView(WorksheetFormView):
    """An form to alter a worksheet in an offering."""
    template = 'templates/worksheet_edit.html'
    permission = 'edit'

    def populate_state(self, state):
        state.existing_worksheet = self.context

    @property
    def offering(self):
        return self.context.offering

    def get_default_data(self, req):
        return {
            'identifier': self.context.identifier,
            'name': self.context.name,
            'assessable': self.context.assessable,
            'data': self.context.data,
            'format': self.context.format
            }

    def get_worksheet_object(self, req, data):
        self.context.identifier = data['identifier']
        self.context.name = data['name']
        self.context.assessable = data['assessable']
        self.context.data = data['data']
        self.context.format = data['format']

        return self.context


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


class ExerciseView(XHTMLView):
    """View of an exercise.

    Primarily to preview and test an exercise without adding it to a
    worksheet for all to see.
    """
    permission = 'edit'
    template = 'templates/exercise.html'

    def populate(self, req, ctx):
        self.plugin_scripts[Plugin] = ['tutorial.js']
        self.plugin_styles[Plugin] = ['tutorial.css']

        ctx['req'] = req
        ctx['mediapath'] = media_url(req, Plugin, 'images/')
        ctx['exercise'] = self.context
        ctx['exercise_fragment'] = present_exercise(
            req, self.context.id)['stream']
        ctx['ExerciseEditView'] = ExerciseEditView
        ctx['ExerciseDeleteView'] = ExerciseDeleteView


class ExerciseEditView(XHTMLView):
    """View for editing a worksheet."""
    permission = 'edit'
    template = 'templates/exercise_edit.html'
    breadcrumb_text = 'Edit'

    def populate(self, req, ctx):
        self.plugin_styles[Plugin] = ['exercise_admin.css']
        self.plugin_scripts[Plugin] = ['exercise_admin.js']

        ctx['mediapath'] = media_url(req, Plugin, 'images/')

        ctx['exercise'] = self.context
        #XXX: These should come from somewhere else

        ctx['var_types'] = {
            'var': 'variable',
            'arg': 'function argument',
            # XXX: wgrant 2010-01-29 bug=514160: Need to
            # restore support for this.
            #'exception': 'exception',
            }
        ctx['part_types'] = {
            'stdout': 'standard output',
            'stderr': 'standard error',
            'result': 'function result',
            'exception': 'raised exception',
            'code': 'code',
            }
        ctx['test_types'] = {'norm': 'normalisation', 'check': 'comparison'}


class ExerciseDeleteView(XHTMLView):
    """View for confirming the deletion of an exercise."""
    
    permission = 'edit'
    template = 'templates/exercise_delete.html'
    
    def populate(self, req, ctx):

        # If post, delete the exercise, or display a message explaining that
        # the exercise cannot be deleted
        if req.method == 'POST':
            try:
                self.context.delete()
                self.template = 'templates/exercise_deleted.html'
            except Exception:
                self.template = 'templates/exercise_undeletable.html'

        # If get, display a delete confirmation page
        else:
            if self.context.worksheet_exercises.count() is not 0:
                self.template = 'templates/exercise_undeletable.html'

        # Variables for the template
        ctx['exercise'] = self.context

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
        ctx['req'] = req
        ctx['exercises'] = req.store.find(Exercise).order_by(Exercise.id)


class Plugin(ViewPlugin, MediaPlugin):
    forward_routes = (root_to_exercise, offering_to_worksheet,
        worksheet_to_worksheetexercise, worksheetexercise_to_exerciseattempts,
        exerciseattempts_to_attempt, subject_to_media)

    reverse_routes = (exercise_url, worksheet_url, worksheetexercise_url,
        exerciseattempts_url, exerciseattempt_url)

    breadcrumbs = {Exercise: ExerciseBreadcrumb,
                   Worksheet: WorksheetBreadcrumb
                  }

    views = [(Offering, ('+worksheets', '+new'), WorksheetAddView),
             (Offering, ('+worksheets', '+edit'), WorksheetsEditView),
             (Worksheet, '+index', WorksheetView),
             (Worksheet, '+edit', WorksheetEditView),
             (ApplicationRoot, ('+exercises', '+index'), ExercisesView),
             (ApplicationRoot, ('+exercises', '+add'), ExerciseAddView),
             (Exercise, '+index', ExerciseView),
             (Exercise, '+edit', ExerciseEditView),
             (Exercise, '+delete', ExerciseDeleteView),
             (SubjectMediaFile, '+index', SubjectMediaView),

             (Offering, ('+worksheets', '+index'), WorksheetsRESTView, 'api'),
             (WorksheetExercise, '+index', WorksheetExerciseRESTView, 'api'),
             (ExerciseAttempts, '+index', AttemptsRESTView, 'api'),
             (ExerciseAttempt, '+index', AttemptRESTView, 'api'),
             (ApplicationRoot, ('+exercises', '+index'), ExercisesRESTView,
              'api'),
             (Exercise, '+index', ExerciseRESTView, 'api'),
             ]

    media = 'media'
    help = {'Tutorial': 'help.html'}
