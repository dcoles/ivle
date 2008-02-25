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

var user_data;

function onload()
{
    revert_settings();
}

/* Fetch the user's details from the server, and populate the page.
 * Returns false. */
function revert_settings()
{
    var callback = function(xhr)
        {
            user = JSON.parse(xhr.responseText);
            populate(user);
        }
    /* Just get details for the logged in user */
    ajax_call(callback, "userservice", "get_user", {}, "GET");
    return false;
}

/* Populate the page with the given user's account details */
function populate(user)
{
    user_data = user;
    /* Plain text elements (non-editable) */
    var login = document.getElementById("login");
    var role = document.getElementById("role");
    var changepassword = document.getElementById("changepassword");
    var notices = document.getElementById("notices");
    /* Textbox (input) elements */
    var nick = document.getElementById("nick");
    var email = document.getElementById("email");

    var text;
    var p;
    var b;
    var table;
    var tbody;
    var tr;
    var td;
    var inputbox;

    /* Clear things */
    dom_removechildren(login);
    dom_removechildren(role);
    dom_removechildren(notices);

    /* Construct the page */

    /* "login" : Full Name (<b>login</b> / studentid) */
    text = user.fullname + " (";
    login.appendChild(document.createTextNode(text));
    text = user.login
    b = document.createElement("b");
    b.appendChild(document.createTextNode(text));
    login.appendChild(b);
    if (user.studentid != null)
        text = " / " + user.studentid + ")"
    else
        text = ")"
    login.appendChild(document.createTextNode(text));

    /* "role" : <p>Your privilege level is <b>rolenm</b>.</p>
     * Unless rolenm is "student"
     */
    if (user.rolenm != "student")
    {
        text = "Your privilege level is ";
        role.appendChild(document.createTextNode(text));
        b = document.createElement("b");
        text = user.rolenm;
        b.appendChild(document.createTextNode(text));
        role.appendChild(b);
        text = ".";
        role.appendChild(document.createTextNode(text));
    }

    /* "nick" and "email" boxes */
    nick.value = user.nick;
    email.value = user.email;

    /* Password change box */
    /* (Only if this user has a local password) */
    if (user.local_password)
    {
        p = document.createElement("h3");
        p.appendChild(document.createTextNode("Change password"))
        changepassword.appendChild(p);
        table = document.createElement("table");
        tbody = document.createElement("tbody");

        tr = document.createElement("tr");
        td = document.createElement("td");
        td.appendChild(document.createTextNode("New password:"))
        tr.appendChild(td);
        td = document.createElement("td");
        inputbox = document.createElement("input");
        inputbox.setAttribute("type", "password");
        inputbox.setAttribute("name", "newpass");
        inputbox.setAttribute("id", "newpass");
        inputbox.setAttribute("size", "40");
        td.appendChild(inputbox)
        tr.appendChild(td);
        tbody.appendChild(tr);

        tr = document.createElement("tr");
        td = document.createElement("td");
        td.appendChild(document.createTextNode("Retype password:"))
        tr.appendChild(td);
        td = document.createElement("td");
        inputbox = document.createElement("input");
        inputbox.setAttribute("type", "password");
        inputbox.setAttribute("name", "repeatpass");
        inputbox.setAttribute("id", "repeatpass");
        inputbox.setAttribute("size", "40");
        td.appendChild(inputbox)
        tr.appendChild(td);
        tbody.appendChild(tr);

        table.appendChild(tbody);
        changepassword.appendChild(table);

        p = document.createElement("p");
        p.appendChild(document.createTextNode("Please type your new password "
            + "twice, to make sure you remember it."))
        changepassword.appendChild(p);
    }

    if (user.pass_exp != null || user.acct_exp != null)
    {
        p = document.createElement("h3");
        text = "Notices";
        p.appendChild(document.createTextNode(text));
        notices.appendChild(p);
        if (user.pass_exp != null)
        {
            p = document.createElement("p");
            /* TODO: Nice passexp */
            var pass_exp = user.pass_exp.toString()
            text = "Your password will expire on " + pass_exp
                + ". You should change it before then to avoid having your "
                + "account disabled.";
            p.appendChild(document.createTextNode(text));
            notices.appendChild(p);
        }
        if (user.acct_exp != null)
        {
            p = document.createElement("p");
            /* TODO: Nice acct_exp */
            var acct_exp = user.acct_exp.toString()
            text = "Your IVLE account will expire on " + acct_exp + ".";
            p.appendChild(document.createTextNode(text));
            notices.appendChild(p);
        }
    }
}

/* Sets the "result" text.
 * iserror (bool) determines the styling.
 */
function set_result(text, iserror)
{
    var p = document.getElementById("result");
    dom_removechildren(p);
    p.appendChild(document.createTextNode(text));
    if (iserror)
        p.setAttribute("class", "error");
    else
        p.removeAttribute("class");
}

/* Writes the settings to the server.
 * Returns false. */
function save_settings()
{
    /* Button (input) elements */
    var save = document.getElementById("save");
    /* Textbox (input) elements */
    try
    {
        var newpass = document.getElementById("newpass");
        var repeatpass = document.getElementById("repeatpass");
    }
    catch (e)
    {
        var newpass = null;
        var repeatpass = null;
    }
    var nick = document.getElementById("nick");
    var email = document.getElementById("email");

    /* Check */
    newpassval = newpass == null ? null : newpass.value;
    repeatpassval = repeatpass == null ? null : repeatpass.value;
    nickval = nick.value;
    emailval = email.value;

    /* Clear the password boxes, even if there are errors later */
    try
    {
        newpass.value = "";
        repeatpass.value = "";
    }
    catch (e)
    {
    }

    if (nickval == "")
    {
        set_result("Display name is empty.", true);
        return false;
    }
    if (newpassval != repeatpassval)
    {
        set_result("Passwords do not match.", true);
        return false;
    }

    /* Disable the heavy-duty supercolliding super button */
    save.setAttribute("disabled", "disabled");
    save.setAttribute("value", "Saving...");
    var callback = function(xhr)
    {
        save.removeAttribute("disabled");
        save.setAttribute("value", "Save");

        if (xhr.status == 200)
        {
            set_result("Successfully updated details.");
            user_data.nick = nickval;
            user_data.email = emailval;
        }
        else
        {
            set_result("There was a problem updating the details."
                + " Your changes have not been saved.");
        }
    }
    data = {
        "login": user_data.login,
        "nick": nickval,
        "email": emailval,
    }
    if (newpassval != null && newpassval != "")
        data['password'] = newpassval;
    ajax_call(callback, "userservice", "update_user", data, "POST");
    return false;
}
