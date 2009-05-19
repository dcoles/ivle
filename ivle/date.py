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
    return dt.strftime("%a %b %d %Y, %l:%M%P")

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

def format_datetime_for_paragraph(datetime_or_seconds):
    """Generate a compact representation of a datetime for use in a paragraph.

    Given a datetime or number of seconds elapsed since the epoch, generates
    a compact string representing the date and time in human-readable form.

    Unlike make_date_nice_short, the time will always be included.

    Also unlike make_date_nice_short, it is suitable for use in the middle of
    a block of prose and properly handles timestamps in the future nicely.
    """

    dt = get_datetime(datetime_or_seconds)
    now = datetime.datetime.now()

    delta = dt - now

    # If the date is earlier than now, we want to either say something like
    # '5 days ago' or '25 seconds ago', 'yesterday at 08:54' or
    # 'on 2009-03-26 at 20:09'.

    # If the time is within one hour of now, we show it nicely in either
    # minutes or seconds.

    if abs(delta).days == 0 and abs(delta).seconds <= 1:
        return 'now'

    if abs(delta).days == 0 and abs(delta).seconds < 60*60:
        if abs(delta) == delta:
            # It's in the future.
            prefix = 'in '
            suffix = ''
        else:
            prefix = ''
            suffix = ' ago'

        # Show the number of minutes unless we are within two minutes.
        if abs(delta).seconds >= 120:
            return (prefix + '%d minutes' + suffix) % (abs(delta).seconds / 60)
        else:
            return (prefix + '%d seconds' + suffix) % (abs(delta).seconds)

    if dt < now:
        if dt.date() == now.date():
            # Today.
            return dt.strftime('today at %l:%M%P')
        elif dt.date() == now.date() - datetime.timedelta(days=1):
            # Yesterday.
            return dt.strftime('yesterday at %l:%M%P')
    elif dt > now:
        if dt.date() == now.date():
            # Today.
            return dt.strftime('today at %l:%M%P')
        elif dt.date() == now.date() + datetime.timedelta(days=1):
            # Tomorrow
            return dt.strftime('tomorrow at %l:%M%P')

    return dt.strftime('on %Y-%m-%d at %l:%M%P')
