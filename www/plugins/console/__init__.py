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

# Plugin: console
# Author: Matt Giuca
# Date: 30/1/2008

# Console plugin. This "mini-app" can be plugged in to another application.
# It exposes two functions: "present" and "insert_scripts_styles".
# These should both be called at the appropriate time by the implementing
# application. See docs on these functions for details.
# Applications also need to call console_init in JavaScript from their own
# onload events.

from common import util

def insert_scripts_styles(scripts, styles):
    """Given 2 lists of strings: scripts and styles. These lists are lists of
    pathnames, as expected on the "scripts" and "styles" attributes of a
    Request object.
    This function appends new strings to the ends of each list, as required by
    this plugin. It does not add duplicates.
    """
    _append_if_absent(scripts,
        "media/common/json2.js",
        "media/common/md5.js",
        "media/common/util.js",
        "media/console/console.js")
    _append_if_absent(styles,
        "media/console/console.css")

def present(req):
    """Writes the HTML for this plugin into a request stream.
    May utilise other properties of the Request object in generating the HTML.
    """
    req.write("""<div id="console_body"><div id="console_body2">
  <div id="console_output">
  </div>
  <div id="console_input">
   <div id="console_inputArea">
   </div>
   <label id="console_prompt">&gt;&gt;&gt;&nbsp;</label>
   <input id="console_inputText"
     type="text" size="80" onkeypress="catch_input(event.keyCode)" />
  </div>
</div></div>
<!-- Console filler, provides extra vertical space to stop the console
     covering over the bottom content -->
<div id="console_filler"></div>
""")

def _append_if_absent(list, *values):
    """Appends an arbitray number of values to a list, but omits values that
    are already contained within the list."""
    for value in values:
        if not value in list:
            list.append(value)
