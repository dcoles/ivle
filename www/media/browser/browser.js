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
    "application/xml" : "text"
};

/* Mapping MIME types to icons, just the file's basename */
type_icons = {
    "text/directory": "dir.png",
    "text/x-python": "py.png"
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
    "revision": "revision.png"
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
    "revision": "Past Permanent file (revision)"
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
    "text/x-python"
];


/* Global variables */

/** The listing object returned by the server as JSON */
file_listing = null;
current_file = null;
current_path = "";

/** Filenames of all files selected
 * (Only used by dir listings, but still needs to be [] for files, so that
 * update_actions knows that nothing is selected).
 */
selected_files = [];

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
function do_action(action, path, args, content_type, ignore_response)
{
    args.action = action;
    /* Callback action, when the server returns */
    var callback = function(response)
        {
            /* Check for action errors reported by the server, and report them
             * to the user */
            var error = response.getResponseHeader("X-IVLE-Action-Error");
            if (error != null)
                alert("Error: " + error.toString() + ".");
            /* Now read the response and set up the page accordingly */
            if (ignore_response != true)
                handle_response(path, response);
        }
    /* Call the server and perform the action. This mutates the server. */
    ajax_call(callback, service_app, path, args, "POST", content_type);
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
    callback = function(response)
        {
            /* Read the response and set up the page accordingly */
            handle_response(path, response, url.args);
        }
    /* Get any query strings */
    url = parse_url(window.location.href);
    
    /* Call the server and request the listing. */
    ajax_call(callback, service_app, path, url.args, "GET");
}

/* Refreshes the current view.
 * Calls navigate on the current path.
 */
function refresh()
{
    navigate(current_path, false);
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
 * \param url_args Arguments dict, for the arguments passed to the URL
 * in the browser's address bar (will be forwarded along).
 */
function handle_response(path, response, url_args)
{
    /* TODO: Set location bar to "path" */
    current_path = path;

    /* Clear away the existing page contents */
    clearpage();

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

    /* This will always return a listing, whether it is a dir or a file.
     */
    var listing = response.responseText;
    /* The listing SHOULD be valid JSON text. Parse it into an object. */
    try
    {
        listing = JSON.parse(listing);
        file_listing = listing.listing;     /* Global */
    }
    catch (e)
    {
        handle_error("The server returned an invalid directory listing");
        return;
    }
    /* Get "." out, it's special */
    current_file = file_listing["."];     /* Global */
    delete file_listing["."];

    /* Check if this is a directory listing or file contents */
    var isdir = response.getResponseHeader("X-IVLE-Return") == "Dir";
    if (isdir)
    {
        handle_dir_listing(path, listing);
    }
    else
    {
        /* Need to make a 2nd ajax call, this time get the actual file
         * contents */
        callback = function(response)
            {
                /* Read the response and set up the page accordingly */
                handle_contents_response(path, response);
            }
        /* Call the server and request the listing. */
        if (url_args)
            args = shallow_clone_object(url_args);
        else
            args = {};
        /* This time, get the contents of the file, not its metadata */
        args['return'] = "contents";
        ajax_call(callback, service_app, path, args, "GET");
    }
    update_actions(isdir);
}

function handle_contents_response(path, response)
{
    /* Treat this as an ordinary file. Get the file type. */
    var content_type = response.getResponseHeader("Content-Type");
    var handler_type = get_handler_type(content_type);
    /* If we're in "edit mode", always treat this file as text */
    would_be_handler_type = handler_type;
    /* handler_type should now be set to either
     * "text", "image", "audio" or "binary". */
    switch (handler_type)
    {
    case "text":
        handle_text(path, response.responseText,
            would_be_handler_type);
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

/** Deletes all "dynamic" content on the page.
 * This returns the page back to the state it is in when the HTML arrives to
 * the browser, ready for another handler to populate it.
 */
function clearpage()
{
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

function update_actions()
{
    var file;
    var numsel = selected_files.length;
    if (numsel <= 1)
    {
        if (numsel == 0)
        {
            /* Display information about the current directory instead */
            filename = path_basename(current_path);
            file = current_file;
        }
        else if (numsel == 1)
        {
            filename = selected_files[0];
            file = file_listing[filename];
        }

        /* Update each action node in the topbar.
         * This includes enabling/disabling actions as appropriate, and
         * setting href/onclick attributes. */
    }

    /* Open */
    /* Available if exactly one file is selected */
    var open = document.getElementById("act_open");
    if (numsel == 1)
    {
        open.setAttribute("class", "choice");
        if (file.isdir)
            open.setAttribute("title",
                "Navigate to this directory in the file browser");
        else
            open.setAttribute("title",
                "Edit or view this file");
        open.setAttribute("href", app_path(this_app, current_path, filename));
    }
    else
    {
        open.setAttribute("class", "disabled");
        open.removeAttribute("title");
        open.removeAttribute("href");
    }

    /* Serve */
    /* Available if exactly one file is selected,
     * and only if this is a file, not a directory */
    var serve = document.getElementById("act_serve");
    if (numsel == 1 && !file.isdir)
    {
        serve.setAttribute("class", "choice");
        serve.setAttribute("href",
            app_path(serve_app, current_path, filename));
    }
    else
    {
        serve.setAttribute("class", "disabled");
        serve.removeAttribute("href");
    }

    /* Run */
    /* Available if exactly one file is selected,
     * and it is a Python file.
     */
    /* TODO */

    /* Download */
    /* Always available.
     * If 0 files selected, download the current file or directory as a ZIP.
     * If 1 directory selected, download it as a ZIP.
     * If 1 non-directory selected, download it.
     * If >1 files selected, download them all as a ZIP.
     */
    var download = document.getElementById("act_download");
    if (numsel <= 1)
    {
        if (numsel == 0)
        {
            download.setAttribute("href",
                app_path(download_app, current_path));
            if (file.isdir)
                download.setAttribute("title",
                    "Download the current directory as a ZIP file");
            else
                download.setAttribute("title",
                    "Download the current file");
        }
        else
        {
            download.setAttribute("href",
                app_path(download_app, current_path, filename));
            if (file.isdir)
                download.setAttribute("title",
                    "Download the selected directory as a ZIP file");
            else
                download.setAttribute("title",
                    "Download the selected file");
        }
    }
    else
    {
        /* Make a query string with all the files to download */
        var dlpath = urlencode_path(app_path(download_app, current_path)) + "?";
        for (var i=0; i<numsel; i++)
            dlpath += "path=" + encodeURIComponent(selected_files[i]) + "&";
        dlpath = dlpath.substr(0, dlpath.length-1);
        download.setAttribute("href", dlpath);
        download.setAttribute("title",
            "Download the selected files as a ZIP file");
    }

    /* Refresh - No changes required */

    /* Publish and Submit */
    /* If this directory is under subversion and selected/unselected file is a
     * directory. */
    var publish = document.getElementById("act_publish");
    var submit = document.getElementById("act_submit");
    if (numsel <= 1 && file.isdir)
    {
        /* TODO: Work out of file is svn'd */
        /* TODO: If this dir is already published, call it "Unpublish" */
        publish.setAttribute("class", "choice");
        publish.removeAttribute("disabled");
        submit.setAttribute("class", "choice");
        submit.removeAttribute("disabled");
    }
    else
    {
        publish.setAttribute("class", "disabled");
        publish.setAttribute("disabled", "disabled");
        submit.setAttribute("class", "disabled");
        submit.setAttribute("disabled", "disabled");
    }

    /* Share */
    /* If exactly 1 non-directory file is selected/opened, and its parent
     * directory is published.
     */
    var share = document.getElementById("act_share");
    if (numsel <= 1 && !file.isdir)
    {
        /* TODO: Work out if parent dir is published */
        share.setAttribute("class", "choice");
        share.removeAttribute("disabled");
    }
    else
    {
        share.setAttribute("class", "disabled");
        share.setAttribute("disabled", "disabled");
    }

    /* Rename */
    /* If exactly 1 file is selected */
    var rename = document.getElementById("act_rename");
    if (numsel == 1)
    {
        rename.setAttribute("class", "choice");
        rename.removeAttribute("disabled");
    }
    else
    {
        rename.setAttribute("class", "disabled");
        rename.setAttribute("disabled", "disabled");
    }

    /* Delete, cut, copy */
    /* If >= 1 file is selected */
    var act_delete = document.getElementById("act_delete");
    var cut = document.getElementById("act_cut");
    var copy = document.getElementById("act_copy");
    if (numsel >= 1)
    {
        act_delete.setAttribute("class", "choice");
        act_delete.removeAttribute("disabled");
        cut.setAttribute("class", "choice");
        cut.removeAttribute("disabled");
        copy.setAttribute("class", "choice");
        copy.removeAttribute("disabled");
    }
    else
    {
        act_delete.setAttribute("class", "disabled");
        act_delete.setAttribute("disabled", "disabled");
        cut.setAttribute("class", "disabled");
        cut.setAttribute("disabled", "disabled");
        copy.setAttribute("class", "disabled");
        copy.setAttribute("disabled", "disabled");
    }

    /* Paste, new file, new directory, upload */
    /* Always enabled (assuming this is a directory) */

    /* Subversion actions */
    /* TODO: Work out when these are appropriate */
    var svnadd = document.getElementById("act_svnadd");
    var svnrevert = document.getElementById("act_svnrevert");
    var svncommit = document.getElementById("act_svncommit");
    if (true)
    {
        svnadd.setAttribute("class", "choice");
        svnadd.removeAttribute("disabled");
        svnrevert.setAttribute("class", "choice");
        svnrevert.removeAttribute("disabled");
        svncommit.setAttribute("class", "choice");
        svncommit.removeAttribute("disabled");
    }

    return;


    /* Unrefactored Code */



    if (1)
    {
        if (file.isdir)
        {
            /* Publish/unpublish */
            if (selected_files.length == 0)
                path = ".";
            else
                path = filename;
            if ("published" in file && file.published)
            {
                p = dom_make_link_elem("p", "Unpublish",
                    "Make it so this directory cannot be seen by anyone but you",
                    null,
                    "return action_unpublish(" + repr(path) + ")");
                sidepanel.appendChild(p);
            }
            else
            {
                p = dom_make_link_elem("p", "Publish",
                    "Make it so this directory can be seen by anyone on the web",
                    null,
                    "return action_publish(" + repr(path) + ")");
                sidepanel.appendChild(p);
            }
        }

        var handler_type = null;
        if ("type" in file)
            handler_type = get_handler_type(file.type);
        /* Action: Use the "files" / "edit" app */
        var path;
        if (selected_files.length == 1)
        {
            /* Don't have "Browse" if this is the current dir */
            if (file.isdir)
                p = dom_make_link_elem("p", "Browse",
                    "Navigate to this directory in the file browser",
                    app_path(this_app, current_path, filename));
            else if (handler_type == "text")
                p = dom_make_link_elem("p", "Edit", "Edit this file",
                    app_path(edit_app, current_path, filename));
            else
                p = dom_make_link_elem("p", "Browse",
                    "View this file in the file browser",
                    app_path(this_app, current_path, filename));
            sidepanel.appendChild(p);
        }

        /* Action: Use the "serve" app */
        /* TODO: Figure out if this file is executable,
         * and change the link to "Run" */
        p = null;
        if (file.isdir || handler_type == "binary") {}
        else
            p = dom_make_link_elem("p", "View",
                "View this file",
                app_path(serve_app, current_path, filename));
        if (p)
            sidepanel.appendChild(p);

        /* Action: Use the "download" app */
        p = null;
        if (selected_files.length == 0)
            path = app_path(download_app, current_path);
        else
            path = app_path(download_app, current_path, filename);
        if (file.isdir)
            p = dom_make_link_elem("p", "Download as zip",
                "Download this directory as a ZIP file", path);
        else
            p = dom_make_link_elem("p", "Download",
                "Download this file to your computer", path);
        if (p)
            sidepanel.appendChild(p);

        if (selected_files.length > 0)
        {   /* Can't rename if we're in it */
            p = dom_make_link_elem("p", "Rename",
                "Change the name of this file", null,
                "return action_rename(" + repr(filename) + ")");
            sidepanel.appendChild(p);
        }
    }
    else
    {
        path = urlencode_path(app_path(download_app, current_path)) + "?";
        for (var i=0; i<selected_files.length; i++)
            path += "path=" + encodeURIComponent(selected_files[i]) + "&";
        path = path.substr(0, path.length-1);
        /* Multiple files selected */
        p = dom_make_link_elem("p", "Download as zip",
            "Download the selected files as a ZIP file", path, null, true);
        sidepanel.appendChild(p);
    }

    /* Common actions */
    if (selected_files.length > 0)
    {
        p = dom_make_link_elem("p", "Delete",
            "Delete the selected files", null,
            "return action_remove(selected_files)");
        sidepanel.appendChild(p);
        p = dom_make_link_elem("p", "Cut",
            "Prepare to move the selected files to another directory", null,
            "return action_cut(selected_files)");
        sidepanel.appendChild(p);
        p = dom_make_link_elem("p", "Copy",
            "Prepare to copy the selected files to another directory", null,
            "return action_copy(selected_files)");
        sidepanel.appendChild(p);
    }
    p = dom_make_link_elem("p", "Paste",
        "Paste the copied or cut files to the current directory", null,
        "return action_paste()");
    sidepanel.appendChild(p);
    p = dom_make_link_elem("p", "Make Directory",
        "Make a new subdirectory in the current directory", null,
        "return action_mkdir()");
    sidepanel.appendChild(p);
    p = dom_make_link_elem("p", "Upload",
        "Upload a file to the current directory", null,
        "return show_uploadpanel()");
    sidepanel.appendChild(p);
    /* The "Upload" button expands the following panel with upload tools */
    /* This panel has a form for submitting the file to, and an iframe to load
     * the target page in (this avoids the entire page being refreshed) */
    div = document.createElement("div");
    div.setAttribute("id", "uploadpanel");
    /* This deliberately hides the upload panel whenever the selection
     * changes. It can be re-shown by clicking "upload". */
    div.setAttribute("style", "display: none;");
    sidepanel.appendChild(div);
    p = dom_make_text_elem("h3", "Upload File");
    div.appendChild(p);
    var form = document.createElement("form");
    form.setAttribute("method", "POST");
    form.setAttribute("enctype", "multipart/form-data");
    form.setAttribute("action", app_path("fileservice", current_path));
    form.setAttribute("target", "upload_iframe");
    div.appendChild(form);
    var input;
    input = document.createElement("input");
    input.setAttribute("type", "hidden");
    input.setAttribute("name", "action");
    input.setAttribute("value", "putfiles");
    form.appendChild(input);

    input = document.createElement("input");
    input.setAttribute("type", "hidden");
    input.setAttribute("name", "path");
    input.setAttribute("value", "");
    form.appendChild(input);

    p = document.createElement("p");
    form.appendChild(p);
    input = document.createElement("input");
    input.setAttribute("type", "file");
    input.setAttribute("name", "data");
    p.appendChild(input);

    p = document.createElement("p");
    form.appendChild(p);
    input = document.createElement("input");
    input.setAttribute("type", "checkbox");
    input.setAttribute("name", "unpack");
    input.setAttribute("value", "true");
    input.setAttribute("checked", "on");
    p.appendChild(input);
    p.appendChild(document.createTextNode(" Unpack zip file"));

    p = document.createElement("p");
    form.appendChild(p);
    input = document.createElement("input");
    input.setAttribute("type", "button");
    input.setAttribute("value", "Hide");
    input.setAttribute("onclick", "show_uploadpanel(false)");
    p.appendChild(input);
    p.appendChild(document.createTextNode(" "));
    input = document.createElement("input");
    input.setAttribute("type", "submit");
    input.setAttribute("value", "Send");
    p.appendChild(input);

    /* Now we create an invisible iframe which will receive the upload.
     * The form submits to fileservice, loading the result into this iframe
     * instead of the whole browser window (this is an alternative to Ajax,
     * since Ajax doesn't allow reading the file from the user's disk).
     * Note this iframe's id is the same as the form's target.
     */
    var upload_iframe = document.createElement("iframe");
    upload_iframe.setAttribute("id", "upload_iframe");
    upload_iframe.setAttribute("name", "upload_iframe");
    upload_iframe.setAttribute("style", "display: none;");
    /* When we get a callback, simply cause a nav to the current path, so we
     * update the directory listing. */
    upload_callback_count = 0;      /* See upload_callback */
    upload_iframe.setAttribute("onload", "upload_callback()");
    div.appendChild(upload_iframe);
    /* END Upload panel */

    if (under_subversion)
    {
        /* TODO: Only show relevant links */
        p = dom_make_text_elem("h3", "Subversion");
        sidepanel.appendChild(p);

        /* TODO: if any selected files are unversioned */
        p = dom_make_link_elem("p", "Add",
            "Schedule the selected temporary files to be added permanently",
            null,
            "return action_add(selected_files)");
        sidepanel.appendChild(p);
        p = dom_make_link_elem("p", "Revert",
            "Restore the selected files back to their last committed state",
            null,
            "return action_revert(selected_files)");
        sidepanel.appendChild(p);
        /* TODO: Update */
        p = dom_make_link_elem("p", "Commit",
            "Commit any changes to the permanent repository",
            null,
            "return action_commit(selected_files)");
        sidepanel.appendChild(p);
    }

}

/** Event handler for when an item of the "More actions..." dropdown box is
 * selected. Performs the selected action. */
function handle_moreactions()
{
    var moreactions = document.getElementById("moreactions");
    if (moreactions.value == "top")
        return;
    var selectedaction = moreactions.value;
    /* Reset to "More actions..." */
    moreactions.selectedIndex = 0;

    /* Now handle the selected action */
    alert("Action: " + selectedaction);
    /* TODO */
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
