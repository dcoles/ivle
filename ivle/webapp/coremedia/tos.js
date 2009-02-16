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
 * Module: Terms of Service
 * Author: Matt Giuca
 * Date: 14/2/2008
 *
 * Client handler for the "Terms of Service" page.
 * (Accepts user's acceptance, and calls usermgt to create the user's jail and
 * activate their account).
 */

/* The user must send this declaration message to ensure they acknowledge the
 * TOS.
 * (This is the exact same string as in userservice).
 */
USER_DECLARATION = {"declaration":
                        "I accept the IVLE Terms of Service"};

/** Creates a "dot dot dot" animation to indicate the client is waiting for a
 * response from the server.
 * This will keep animating forever.
 * Returns a DOM element which will automatically have its contents changed on
 * intervals.
 */
function make_dots_anim()
{
    var p = document.createElement("p");
    anim_dots = document.createTextNode("");
    p.appendChild(anim_dots);
    setInterval("anim_dots.data = updateDots(anim_dots.data);", 500);
    return p;
}
function updateDots(text)
{
    if (text.length >= 4)
        return ".";
    else
        return text + ".";
}

function accept_license()
{
    /* The user has accepted the license.
     * We need to call usermgt to tell it the good news.
     * It will go away and make the user's jail and activate the account in
     * the DB, among other things.
     * This could take awhile (which is why we're using Ajax).
     * We need to wait on this page for the server's response.
     */
    /* Start by clearing away these buttons. */
    var tos_acceptbuttons = document.getElementById("tos_acceptbuttons");
    dom_removechildren(tos_acceptbuttons);
    /* Print a "please wait" message */
    tos_acceptbuttons.appendChild(dom_make_text_elem("p",
        "IVLE is now setting up your environment. Please wait..."));
    tos_acceptbuttons.appendChild(make_dots_anim());
    /* Make the Ajax request */
    ajax_call(handle_accept_response, "userservice", "activate_me",
        USER_DECLARATION, "POST")
}

function handle_accept_response(xhr)
{
    /* TEMP */
    var tos_acceptbuttons = document.getElementById("tos_acceptbuttons");
    dom_removechildren(tos_acceptbuttons);

    try
    {
        response = JSON.parse(xhr.responseText);
    }
    catch (e)
    {
        response = {'response': 'parse-failure'};
    }

    if (response.response == 'usrmgt-failure')
    {
    tos_acceptbuttons.appendChild(dom_make_text_elem("p",
        "Error connecting to User Management server. Please try again later.")); 
    }
    else if (response.response == 'parse-failure')
    {
    tos_acceptbuttons.appendChild(dom_make_text_elem("p",
        "Error connecting to server. Please try again later. "));
    }
    else
    {
        /* Refresh the page; as the user is now (apparently) logged in */
        window.location.href = window.location.href;
    }
}

function decline_license()
{
    /* Redirect to the logout page */
    window.location.href = app_path("logout");
}
