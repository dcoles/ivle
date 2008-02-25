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

# App: settings
# Author: Matt Giuca
# Date: 25/2/2008

# User settings UI
# (Also provides UI for administering users, given sufficient privileges).

from common import util

def handle(req):
    """Handler for the Settings application."""

    # Set request attributes
    req.content_type = "text/html"
    # These files don't really exist - just a test of our linking
    # capabilities
    req.styles = [
        "media/settings/settings.css",
    ]
    req.scripts = [
        "media/settings/settings.js",
        "media/common/json2.js",
        "media/common/util.js",
    ]
    req.write_html_head_foot = True     # Have dispatch print head and foot

    # Start writing data
    req.write("""<div id="ivle_padding">

  <h2>User Profile</h2>
  <p><span id="login"></span></p>
  <p id="role"></p>
  <h3>Change settings</h3>
  <form action="">
    <table>
      <tr><td>Display name:</td><td><input type="text"
            name="nick" id="nick" size="40" /></td></tr>
      <tr><td>Email address:</td><td><input type="text"
            name="email" id="email" size="40" /></td></tr>
    </table>
    <div id="changepassword"></div>
    <p id="result"></p>
    <p>
      <input value="Save" onclick="return save_settings()" id="save"
          type="submit" />
      <input value="Revert" onclick="return revert_settings()" id="revert"
          type="reset" />
    </p>
  </form>

  <div id="notices"></div>
</div>
""")
