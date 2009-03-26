# IVLE
# Copyright (C) 2008 The University of Melbourne
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

'''Utilities for making nice, human readable dates.'''

import time
import datetime

def get_datetime(datetime_or_seconds):
    '''Return the given datetime, or convert the given seconds since epoch.'''
    if type(datetime_or_seconds) is datetime.datetime:
        return datetime_or_seconds
    return datetime.datetime.fromtimestamp(datetime_or_seconds)

def make_date_nice(datetime_or_seconds):
    """Generate a full human-readable representation of a date and time.

    Given a datetime or number of seconds elapsed since the epoch,
    generates a string representing the date/time in human-readable form.
    "ddd mmm dd, yyyy h:m a"
    """
    dt = get_datetime(datetime_or_seconds)
    return dt.strftime("%a %b %d %Y, %I:%M %p")

def make_date_nice_short(datetime_or_seconds):
    """Generate a very compact human-readable representation of a date.

    Given a datetime or number of seconds elapsed since the epoch,
    generates a string representing the date in human-readable form.
    Does not include the time.
    """

    dt = get_datetime(datetime_or_seconds)
    now = datetime.datetime.now()

    # Use a "naturalisation" algorithm.
    delta = now - dt

    if delta.days <= 5:
        # Dates today or yesterday, return "today" or "yesterday".
        if delta.days == 0:
            return "Today"
        elif delta.days == 1:
            return "Yesterday"
        else:
            # Dates in the last 5 days, return "n days ago".
            return str(delta.days) + " days ago"
    # Other dates, return a short date format.
    # If within the same year, omit the year (mmm dd)
    if dt.year == now.year:
        return dt.strftime("%b %d")
    # Else, include the year (mmm dd, yyyy)
    else:
        return dt.strftime("%b %d, %Y")
