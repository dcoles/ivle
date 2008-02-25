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
 * Module: Settings (Client-side JavaScript)
 * Author: Matt Giuca
 * Date: 25/2/2008
 */

function onload()
{
    populate();
}

/* Populate the page with this user's account details */
function populate()
{
    var callback = function(xhr)
        {
            user = JSON.parse(xhr.responseText);
        }
    /* Just get details for the logged in user */
    ajax_call(callback, "userservice", "get_user", {}, "GET");
}
