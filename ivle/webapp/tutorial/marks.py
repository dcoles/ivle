# IVLE
# Copyright (C) 2007-2010 The University of Melbourne
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

# Author: Matt Giuca

"""Worksheet marks reporting functionality.

Displays students' worksheet marks to users with sufficient privileges.
"""

import datetime

from ivle.webapp.base.xhtml import XHTMLView
from ivle.webapp.media import media_url

class WorksheetsMarksView(XHTMLView):
    """View for presenting all students' individual marks for worksheets."""
    permission = 'view_worksheet_marks'
    template = 'templates/worksheets_marks.html'
    tab = 'subjects'

    def populate(self, req, ctx):
        error = None
        ctx['context'] = self.context

        # User may supply a "cutoff date" to calculate marks as of that date
        # Default to current time
        cutoff = datetime.datetime.now()
        data = dict(req.get_fieldstorage())
        if data.get('cutoff') is not None:
            try:
                cutoff = datetime.datetime.strptime(data.get('cutoff'),
                                                    "%Y-%m-%d %H:%M:%S")
            except ValueError:
                error = (
                    "Invalid date format: '%s' (must be YYYY-MM-DD H:M:S)."
                        % data.get('cutoff'))
        ctx['cutoff'] = cutoff
        ctx['error'] = error
