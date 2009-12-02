/* IVLE - Informatics Virtual Learning Environment
 * Copyright (C) 2007-2008 The University of Melbourne
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 *
 * Module: Subversion Log
 * Author: David Coles
 * Date: 2/12/2009
 */

browser_app = "files";

/** Called when the page loads initially */
function log_init()
{
    this_app = "svnlog";
    current_path = get_path();
}

function update_revision(button, revid) {
    button.disabled = true;
    do_action("svnupdate", current_path, {'path':'.', 'revision': revid},
        null, function(path, response) {
            var error = response.getResponseHeader("X-IVLE-Action-Error");
            if(error == null || error == "")
            {
                /** If no error, return to current_path in browser */
                window.location.href = make_path(browser_app)+'/'+path;
            }
            else
            {
                /** Otherwise stay here */
                button.disabled = false;
            }
        });
}
