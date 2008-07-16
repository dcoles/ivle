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

# Module: Date utilities
# Author: William Grant
# Date: 16/07/2008

import time

seconds_per_day = 86400 # 60 * 60 * 24
if time.daylight:
    timezone_offset = time.altzone
else:
    timezone_offset = time.timezone

def make_date_nice(seconds_since_epoch):
    """Given a number of seconds elapsed since the epoch,
    generates a string representing the date/time in human-readable form.
    "ddd mmm dd, yyyy h:m a"
    """
    #return time.ctime(seconds_since_epoch)
    return time.strftime("%a %b %d %Y, %I:%M %p",
        time.localtime(seconds_since_epoch))

def make_date_nice_short(seconds_since_epoch):
    """Given a number of seconds elapsed since the epoch,
    generates a string representing the date in human-readable form.
    Does not include the time.
    This function generates a very compact representation."""
    # Use a "naturalisation" algorithm.
    days_ago = (int(time.time() - timezone_offset) / seconds_per_day
        - int(seconds_since_epoch - timezone_offset) / seconds_per_day)
    if days_ago <= 5:
        # Dates today or yesterday, return "today" or "yesterday".
        if days_ago == 0:
            return "Today"
        elif days_ago == 1:
            return "Yesterday"
        else:
            return str(days_ago) + " days ago"
        # Dates in the last 5 days, return "n days ago".
    # Other dates, return a short date format.
    # If within the same year, omit the year (mmm dd)
    if time.localtime(seconds_since_epoch).tm_year==time.localtime().tm_year:
        return time.strftime("%b %d", time.localtime(seconds_since_epoch))
    # Else, include the year (mmm dd, yyyy)
    else:
        return time.strftime("%b %d, %Y", time.localtime(seconds_since_epoch))
