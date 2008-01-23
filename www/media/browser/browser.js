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
 * Module: File Browser (client)
 * Author: Matt Giuca
 * Date: 11/1/2008
 */

/* Url names for apps */
this_app = "files";
edit_app = "edit";
service_app = "fileservice";
serve_app = "serve";
download_app = "download";

/* Mapping MIME types onto handlers.
 * "text" : When navigating to a text file, the text editor is opened.
 * "image" : When navigating to an image, the image is displayed (rather than
 *              going to the text editor).
 * "audio" : When navigating to an audio file, a "play" button is presented.
 * "binary" : When navigating to a binary file, offer it as a download through
 *              "serve".
 *
 * If a file is not on the list, its default action is determined by the first
 * part of its content type, where "text/*", "image/*" and "audio/*" are
 * treated as above, and other types are simply treated as binary.
 */
type_handlers = {
    "application/x-javascript" : "text",
    "application/javascript" : "text",
    "application/json" : "text",
    "application/xml" : "text",
};

/* Mapping MIME types to icons, just the file's basename */
type_icons = {
    "text/directory": "dir.png",
    "text/x-python": "py.png",
};

default_type_icon = "txt.png";

/* Relative to IVLE root */
type_icons_path = "media/images/mime";
type_icons_path_large = "media/images/mime/large";

/* Mapping SVN status to icons, just the file's basename */
svn_icons = {
    "unversioned": null,
    "normal": "normal.png",
    "added": "added.png",
    "missing": "missing.png",
    "deleted": "deleted.png",
    "modified": "modified.png",
};

/* Mapping SVN status to "nice" strings */
svn_nice = {
    "unversioned": "Temporary file",
    "normal": "Permanent file",
    "added": "Temporary file (scheduled to be added)",
    "missing": "Permanent file (missing)",
    "deleted": "Permanent file (scheduled for deletion)",
    "replaced": "Permanent file (replaced)",
    "modified": "Permanent file (modified)",
    "merged": "Permanent file (merged)",
    "conflicted": "Permanent file (conflicted)",
};

default_svn_icon = null;
default_svn_nice = "Unknown status";

svn_icons_path = "media/images/svn";

published_icon = "media/images/interface/published.png";

/* List of MIME types considered "executable" by the system.
 * Executable files offer a "run" link, implying that the "serve"
 * application can interpret them.
 */
types_exec = [
    "text/x-python",
];


/* Global variables */

current_path = "";

/** Calls the server using Ajax, performing an action on the server side.
 * Receives the response from the server and performs a refresh of the page
 * contents, updating it to display the returned data (such as a directory
 * listing, file preview, or editor pane).
 * Always makes a POST request.
 * No return value.
 *
 * \param action String. Name of the action to perform, as defined in the
 *     fileservice API.
 * \param path URL path to make the request to, within the application.
 * \param args Argument object, as described in util.parse_url and friends.
 *      This should contain the arguments to the action, but NOT the action
 *      itself. (Also a minor side-effect; the "args" object will be mutated
 *      to include the action attribute).
 * \param content_type String, optional.
 *      May be "application/x-www-form-urlencoded" or "multipart/form-data".
 *      Defaults to "application/x-www-form-urlencoded".
 *      "multipart/form-data" is recommended for large uploads.
 */
function do_action(action, path, args, content_type)
{
    args.action = action;
    /* Call the server and perform the action. This mutates the server. */
    response = ajax_call(service_app, path, args, "POST", content_type);
    /* Check for action errors reported by the server, and report them to the
     * user */
    error = response.getResponseHeader("X-IVLE-Action-Error");
    if (error != null)
        alert("Error: " + error.toString() + ".");
    /* Now read the response and set up the page accordingly */
    handle_response(path, response);
}

/** Calls the server using Ajax, requesting a directory listing. This should
 * not modify the server in any way. Receives the response from the server and
 * performs a refresh of the page contents, updating it to display the
 * returned data (such as a directory listing, file preview, or editor pane).
 * Called "navigate", can also be used for a simple refresh.
 * Always makes a GET request.
 * No return value.
 * \param editmode Optional boolean. If true, then the user navigated here
 * with an "edit" URL so we should favour using the editor.
 */
function navigate(path, editmode)
{
    /* Call the server and request the listing. This mutates the server. */
    response = ajax_call(service_app, path, null, "GET");
    /* Now read the response and set up the page accordingly */
    handle_response(path, response, editmode);
}

/** Determines the "handler type" from a MIME type.
 * The handler type is a string, either "text", "image", "audio" or "binary".
 */
function get_handler_type(content_type)
{
    if (!content_type)
        return null;
    if (content_type in type_handlers)
        return type_handlers[content_type];
    else
    {   /* Based on the first part of the MIME type */
        var handler_type = content_type.split('/')[0];
        if (handler_type != "text" && handler_type != "image" &&
            handler_type != "audio")
            handler_type = "binary";
        return handler_type;
    }
}

/** Given an HTTP response object, cleans up and rebuilds the contents of the
 * page using the response data. This does not navigate away from the page, it
 * merely rebuilds most of the data.
 * Note that depending on the type of data returned, this could result in a
 * directory listing, an image preview, an editor pane, etc.
 * Figures out the type and calls the appropriate function.
 * \param path URL path which the request was made for. This can (among other
 * things) be used to update the URL in the location bar.
 * \param response XMLHttpRequest object returned by the server. Should
 * contain all the response data.
 * \param editmode Optional boolean. If true, then the user navigated here
 * with an "edit" URL so we should favour using the editor.
 */
function handle_response(path, response, editmode)
{
    /* TODO: Set location bar to "path" */
    current_path = path;

    /* Clear away the existing page contents */
    clearpage();
    /* Display the path at the top, for navigation */
    presentpath(path);

    /* Check the status, and if not 200, read the error and handle this as an
     * error. */
    if (response.status != 200)
    {
        var error = response.getResponseHeader("X-IVLE-Return-Error");
        if (error == null)
            error = response.statusText;
        handle_error(error);
        return;
    }

    /* Check if this is a directory listing or file contents */
    var isdir = response.getResponseHeader("X-IVLE-Return") == "Dir";
    if (!editmode && isdir)
    {
        var listing = response.responseText;
        /* The listing SHOULD be valid JSON text. Parse it into an object. */
        try
        {
            listing = JSON.parse(listing);
        }
        catch (e)
        {
            handle_error("The server returned an invalid directory listing");
            return;
        }
        handle_dir_listing(path, listing);
    }
    else
    {
        /* Treat this as an ordinary file. Get the file type. */
        var content_type = response.getResponseHeader("Content-Type");
        var handler_type = get_handler_type(content_type);
        /* If we're in "edit mode", always treat this file as text */
        would_be_handler_type = handler_type;
        if (editmode) handler_type = "text";
        /* handler_type should now be set to either
         * "text", "image", "audio" or "binary". */
        switch (handler_type)
        {
        case "text":
            if (isdir)
            {
                handle_text(path_join(path, "untitled"), "",
                    would_be_handler_type);
            }
            else
            {
                handle_text(path, response.responseText,
                    would_be_handler_type);
            }
            break;
        case "image":
            /* TODO: Custom image handler */
            handle_binary(path, response.responseText);
            break;
        case "audio":
            /* TODO: Custom audio handler */
            handle_binary(path, response.responseText);
            break;
        case "binary":
            handle_binary(path);
            break;
        }
    }
}

/** Deletes all "dynamic" content on the page.
 * This returns the page back to the state it is in when the HTML arrives to
 * the browser, ready for another handler to populate it.
 */
function clearpage()
{
    dom_removechildren(document.getElementById("path"));
    dom_removechildren(document.getElementById("filesbody"));
}

/** Deletes all "dynamic" content on the page necessary to navigate from
 * one directory listing to another (does not clear as much as clearpage
 * does).
 * This is the equivalent of calling clearpage() then
 * setup_for_dir_listing(), assuming the page is already on a dir listing.
 */
function clearpage_dir()
{
    dom_removechildren(document.getElementById("path"));
    dom_removechildren(document.getElementById("files"));
    dom_removechildren(document.getElementById("sidepanel"));
}

/** Sets the mode to either "file browser" or "text editor" mode.
 * This modifies the window icon, and selected tab.
 * \param editmode If True, editor mode. Else, file browser mode.
 */
function setmode(editmode)
{
    /* Find the DOM elements for the file browser and editor tabs */
    var tabs = document.getElementById("apptabs");
    var tab_files = null;
    var tab_edit = null;
    var a;
    var href;
    for (var i=0; i<tabs.childNodes.length; i++)
    {
        /* Find the href of the link within */
        if (!tabs.childNodes[i].getElementsByTagName) continue;
        a = tabs.childNodes[i].getElementsByTagName("a");
        if (a.length == 0) continue;
        href = a[0].getAttribute("href");
        if (href == null) continue;
        if (endswith(href, this_app))
            tab_files = tabs.childNodes[i];
        else if (endswith(href, edit_app))
            tab_edit = tabs.childNodes[i];
    }

    if (editmode)
    {
        tab_files.removeAttribute("class");
        tab_edit.setAttribute("class", "thisapp");
    }
    else
    {
        tab_edit.removeAttribute("class");
        tab_files.setAttribute("class", "thisapp");
    }
}

/*** HANDLERS for different types of responses (such as dir listing, file,
 * etc). */

function handle_error(message)
{
    setmode(false);
    var files = document.getElementById("filesbody");
    var txt_elem = dom_make_text_elem("div", "Error: "
        + message.toString() + ".")
    txt_elem.setAttribute("class", "padding error");
    files.appendChild(txt_elem);
}

/** Presents a path list (address bar inside the page) for clicking.
 */
function presentpath(path)
{
    var dom_path = document.getElementById("path");
    var href_path = make_path(this_app);
    var nav_path = "";
    var dir;

    /* Also set the document title */
    document.title = path_basename(path) + " - IVLE";
    /* Create all of the paths */
    var pathlist = path.split("/");
    for (var i=0; i<pathlist.length; i++)
    {
        dir = pathlist[i];
        if (dir == "") continue;
        /* Make an 'a' element */
        href_path = path_join(href_path, dir);
        nav_path = path_join(nav_path, dir);
        var link = dom_make_link_elem("a", dir, "Navigate to " + nav_path,
                href_path/*, "navigate(" + repr(href_path) + ")"*/);
        dom_path.appendChild(link);
        dom_path.appendChild(document.createTextNode("/"));
    }
    dom_path.removeChild(dom_path.lastChild);
}

/** Given a mime type, returns the path to the icon.
 * \param type String, Mime type.
 * \param sizelarge Boolean, optional.
 * \return Path to the icon. Has applied make_path, so it is relative to site
 * root.
 */
function mime_type_to_icon(type, sizelarge)
{
    var filename;
    if (type in type_icons)
        filename = type_icons[type];
    else
        filename = default_type_icon;
    if (sizelarge)
        return make_path(path_join(type_icons_path_large, filename));
    else
        return make_path(path_join(type_icons_path, filename));
}

/** Given an svnstatus, returns the path to the icon.
 * \param type String, svn status.
 * \return Path to the icon. Has applied make_path, so it is relative to site
 * root. May return null to indicate no SVN icon.
 */
function svnstatus_to_icon(svnstatus)
{
    var filename;
    if (svnstatus in svn_icons)
        filename = svn_icons[svnstatus];
    else
        filename = default_svn_icon;
    if (filename == null) return null;
    return make_path(path_join(svn_icons_path, filename));
}

/** Given an svnstatus, returns the "nice" string.
 */
function svnstatus_to_string(svnstatus)
{
    if (svnstatus in svn_nice)
        return svn_nice[svnstatus];
    else
        return default_svn_nice;
}

/** Displays a download link to the binary file.
 */
function handle_binary(path)
{
    setmode(false);
    var files = document.getElementById("filesbody");
    var div = document.createElement("div");
    files.appendChild(div);
    div.setAttribute("class", "padding");
    var download_link = app_path(download_app, path);
    var par1 = dom_make_text_elem("p",
        "The file " + path + " is a binary file. To download this file, " +
        "click the following link:");
    var par2 = dom_make_link_elem("p",
        "Download " + path, "Download " + path, download_link);
    div.appendChild(par1);
    div.appendChild(par2);
}

/** Called when the page loads initially.
 */
window.onload = function()
{
    /* Navigate (internally) to the path in the URL bar.
     * This causes the page to be populated with whatever is at that address,
     * whether it be a directory or a file.
     */
    var path = parse_url(window.location.href).path;
    /* Strip out root_dir + "/files" from the front of the path */
    var strip = make_path(this_app);
    var editmode = false;
    if (path.substr(0, strip.length) == strip)
        path = path.substr(strip.length+1);
    else
    {
        /* See if this is an edit path */
        strip = make_path(edit_app);
        if (path.substr(0, strip.length) == strip)
        {
            path = path.substr(strip.length+1);
            editmode = true;
        }
    }

    if (path.length == 0)
    {
        /* Navigate to the user's home directory by default */
        /* TEMP? */
        path = username;
    }

    navigate(path, editmode);
}
