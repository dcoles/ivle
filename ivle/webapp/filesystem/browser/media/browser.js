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
 * "video" : When navigation to a video file, a "play" button is presented.
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
    "application/ogg" : "audio"
};

/* Mapping MIME types to icons, just the file's basename */
type_icons = {
    "text/directory": "dir.png",
    "text/x-python": "py.png"
};

default_type_icon = "txt.png";

/* Relative to IVLE root */
type_icons_path = "+media/ivle.webapp.core/images/mime";
type_icons_path_large = "+media/ivle.webapp.core/images/mime/large";

/* Mapping SVN status to icons, just the file's basename */
svn_icons = {
    "unversioned": "unversioned.png",
    "ignored": null,                    /* Supposed to be innocuous */
    "normal": "normal.png",
    "added": "added.png",
    "missing": "missing.png",
    "deleted": "deleted.png",
    "replaced": "replaced.png",
    "modified": "modified.png",
    "conflicted": "conflicted.png",
    "revision": "revision.png"
};

/* Mapping SVN status to "nice" strings */
svn_nice = {
    "unversioned": "Temporary file",
    "ignored": "Temporary file (ignored)",
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

svn_icons_path = "+media/ivle.webapp.core/images/svn";

published_icon = "+media/ivle.webapp.core/images/interface/published.png";

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
current_revision = null;
current_path = "";

/** Filenames of all files selected
 * (Only used by dir listings, but still needs to be [] for files, so that
 * update_actions knows that nothing is selected).
 */
selected_files = [];

upload_callback_count = 0;      /* See upload_callback */

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
 * \param callback, optional.
 *      A callback function for after the action has been handled.
 */
function do_action(action, path, args, content_type, callback)
{
    args.action = action;
    /* Callback action, when the server returns */
    var callback_inner = function(response)
        {
            /* Check for action errors reported by the server, and report them
             * to the user */
            var error = response.getResponseHeader("X-IVLE-Action-Error");
            if (error != null && error != "")
                /* Note: This header (in particular) comes URI-encoded, to
                 * allow multi-line error messages. Decode */
                alert("Error: " + decodeURIComponent(error.toString()) + ".");
            /* Now read the response and set up the page accordingly */
            if (callback != null)
                callback(path, response);
        }
    /* Call the server and perform the action. This mutates the server. */
    ajax_call(callback_inner, service_app, path, args, "POST", content_type);
}

/** Calls the server using Ajax, requesting a directory listing. This should
 * not modify the server in any way. Receives the response from the server and
 * performs a refresh of the page contents, updating it to display the
 * returned data (such as a directory listing, file preview, or editor pane).
 * Called "navigate", can also be used for a simple refresh.
 * Always makes a GET request.
 * No return value.
 */
function navigate(path)
{
    callback = function(response)
        {
            /* Read the response and set up the page accordingly */
            handle_response(path, response, false, url.args);
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
    if (maybe_save('All changes since the last save will be lost!'))
        navigate(current_path);
}

/** Determines the "handler type" from a MIME type.
 * The handler type is a string, either "text", "image", "video", "audio" or 
 * "binary".
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
            handler_type != "video" && handler_type != "audio")
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
 * \param is_action Boolean. True if this is the response to an action, false
 * if this is the response to a simple listing. This is used in handling the
 * error.
 * \param url_args Arguments dict, for the arguments passed to the URL
 * in the browser's address bar (will be forwarded along).
 */
function handle_response(path, response, is_action, url_args)
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

    var subjects = null;
    /* Remove trailing slash (or path==username won't compare properly) */
    if (path[path.length-1] == "/")
        path = path.substr(0, path.length-1);
    var top_level_dir = path==username;
    if (top_level_dir)
    {
        var req = ajax_call(null, "userservice", "get_enrolments", null, "GET")
        subjects = decode_response(req);
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
        if (is_action)
        {
            var err = document.createElement("div");
            var p = dom_make_text_elem("p", "Error: "
                    + "There was an unexpected server error processing "
                    + "the selected command.");
            err.appendChild(p);
            p = dom_make_text_elem("p", "If the problem persists, please "
                    + "contact the system administrator.")
            err.appendChild(p);
            p = document.createElement("p");
            var refresh = document.createElement("input");
            refresh.setAttribute("type", "button");
            refresh.setAttribute("value", "Back to file view");
            refresh.setAttribute("onclick", "refresh()");
            p.appendChild(refresh);
            err.appendChild(p);
            handle_error(err);
        }
        else
        {
            var err = document.createElement("div");
            var p = dom_make_text_elem("p", "Error: "
                    + "There was an unexpected server error retrieving "
                    + "the requested file or directory.");
            err.appendChild(p);
            p = dom_make_text_elem("p", "If the problem persists, please "
                    + "contact the system administrator.")
            err.appendChild(p);
            handle_error(err);
        }
        return;
    }
    /* Get "." out, it's special */
    current_file = file_listing["."];     /* Global */
    delete file_listing["."];

    if ('revision' in listing)
    {
        current_revision = listing.revision;
    }

    /* Check if this is a directory listing or file contents */
    var isdir = response.getResponseHeader("X-IVLE-Return") == "Dir";
    if (isdir)
    {
        setup_for_listing();
        if (top_level_dir)
        {
            /* Top-level dir, with subjects */
            special_home_listing(listing, subjects, path);
        }
        else
        {
            /* Not the top-level dir. Do a normal dir listing. */
            handle_dir_listing(path, listing.listing);
        }
    }
    else
    {
        /* Read the response and set up the page accordingly */
        var content_type = current_file.type;
        handle_contents_response(path, content_type, url_args);

    }
    update_actions(isdir);
}

function handle_contents_response(path, content_type)
{
    /* Treat this as an ordinary file. Get the file type. */
    //var content_type = response.getResponseHeader("Content-Type");
    var handler_type = get_handler_type(content_type);
    /* handler_type should now be set to either
     * "text", "image", "video", "audio" or "binary". */
    switch (handler_type)
    {
    case "text":
        handle_text(path, content_type);
        break;
    case "image":
        handle_image(path);
        break;
    case "video":
        handle_video(path, content_type);
        break;
    case "audio":
        handle_audio(path, content_type);
        break;
    case "binary":
        handle_binary(path);
        break;
    }
}

/* Called when a form upload comes back (from an iframe).
 * Refreshes the page.
 */
function upload_callback()
{
    /* This has a pretty nasty hack, which happens to work.
     * upload_callback is set as the "onload" callback for the iframe which
     * receives the response from the server for uploading a file.
     * This means it gets called twice. Once when initialising the iframe, and
     * a second time when the actual response comes back.
     * All we want to do is call navigate to refresh the page. But we CAN'T do
     * that on the first load or it will just go into an infinite cycle of
     * refreshing. We need to refresh the page ONLY on the second refresh.
     * upload_callback_count is reset to 0 just before the iframe is created.
     */
    upload_callback_count++;
    if (upload_callback_count >= 2)
    {
        myFrame = frames['upload_iframe'].document;
        /* Browsers will turn the raw returned JSON into an HTML document. We
         * need to get the <pre> from inside the <body>, and look at its text.
         */
        var pre = myFrame.firstChild.getElementsByTagName(
            'body')[0].firstChild;
        var data = pre.innerText || pre.textContent;
        data = JSON.parse(data);
        if ('Error' in data)
            alert("Error: " + decodeURIComponent(data['Error']));
        document.getElementsByName('data')[0].value = '';
        refresh();
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

/* Checks if a file needs to be saved. If it does, the user will be asked
 * if they want to continue anyway. The caller must specify a warning
 * sentence which indicates the consequences of continuing.
 * Returns true if we should continue, and false if we should not.
 */
function maybe_save(warning)
{
    if (warning == null) warning = '';
    if (current_file == null || current_file.isdir) return true;
    if (document.getElementById("save_button").disabled) return true;
    return confirm("This file has unsaved changes. " + warning +
                   "\nAre you sure you wish to continue?");
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

/*** HANDLERS for different types of responses (such as dir listing, file,
 * etc). */

/* handle_error.
 * message may either be a string, or a DOM node, which will be placed inside
 * a div.
 */
function handle_error(message)
{
    var files = document.getElementById("filesbody");
    var txt_elem;
    if (typeof(message) == "string")
    {
        txt_elem = dom_make_text_elem("div", "Error: "
                   + message.toString() + ".")
    }
    else
    {
        /* Assume message is a DOM node */
        txt_elem = document.createElement("div");
        txt_elem.appendChild(message);
    }
    txt_elem.setAttribute("class", "padding error");
    files.appendChild(txt_elem);
}

/** Given a path, filename and optional revision, returns a URL to open that
 *  revision of that file.
 */
function build_revision_url(path, filename, revision)
{
    bits = {'path': app_path(this_app, path, filename)};
    if (current_revision)
    {
        bits['query_string'] = 'r=' + revision;
    }
    return build_url(bits);
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

/** Returns true if a file is versioned (not unversioned or ignored).
 */
function svnstatus_versioned(svnstatus)
{
    return svnstatus != "unversioned" && svnstatus != "ignored";
}

/** Displays a download link to the binary file.
 */
function handle_binary(path)
{
    // Disable save button
    using_codepress = false;
    disable_save_if_safe();

    // Show download link
    var files = document.getElementById("filesbody");
    var div = document.createElement("div");
    files.appendChild(div);
    div.setAttribute("class", "padding");
    var download_link = app_url(download_app, path);
    var par1 = dom_make_text_elem("p",
        "The file " + path + " is a binary file. To download this file, " +
        "click the following link:");
    var par2 = dom_make_link_elem("p",
        "Download " + path, "Download " + path, download_link);
    div.appendChild(par1);
    div.appendChild(par2);
}

/** Displays an image file.
 */
function handle_image(path)
{
    /* Disable save button */
    using_codepress = false;
    disable_save_if_safe();

    /* URL */
    var url = app_url(download_app, path);

    /* Image Preview */
    var img = $("<img />");
    img.attr("alt", path);
    img.attr("src", url);

    /* Show Preview */
    var div = $('<div class="padding" />');
    div.append('<h1>Image Preview</h1>');
    div.append(img);
    $("#filesbody").append(div);
}

/** Displays a video.
 */
function handle_video(path, type)
{
    /* Disable save button and hide the save panel */
    using_codepress = false;
    disable_save_if_safe();

    /* URL */
    var url = app_url(download_app, path);

    /* Fallback Download Link */
    var link = $('<p>Could not display video in browser.<p><p><a /></p>');
    var a = link.find('a');
    a.attr("href", url);
    a.text("Download " + path);

    /* Fallback Object Tag */
    var obj = $('<object />');
    obj.attr("type", type);
    obj.attr("data", url);
    obj.append(link);

    /* HTML 5 Video Tag */
    var video = $('<video controls="true" autoplay="true" />');
    video.attr("src", url);
    var support = video[0].canPlayType && video[0].canPlayType(type);
    if (support != "probably" && support != "maybe") {
        // Use Fallback
        video = obj;
    }

    /* Show Preview */
    var div = $('<div class="padding" />');
    div.append('<h1>Video Preview</h1>');
    div.append(video);
    $("#filesbody").append(div);
}

/** Display audio content
 */
function handle_audio(path, type)
{
    /* Disable save button and hide the save panel */
    using_codepress = false;
    disable_save_if_safe();

    /* URL */
    var url = app_url(download_app, path);

    /* Fallback Download Link */
    var link = $('<p>Could not display audio in browser.<p><p><a /></p>');
    var a = link.find('a');
    a.attr("href", url);
    a.text("Download " + path);

    /* Fallback Object Tag */
    var obj = $('<object />');
    obj.attr("type", type);
    obj.attr("data", url);
    obj.append(link);

    /* HTML 5 Audio Tag */
    var audio = $('<audio controls="true" autoplay="true" />');
    audio.attr("src", url);
    var support = audio[0].canPlayType && audio[0].canPlayType(type);
    if (support != "probably" && support != "maybe") {
        // Use Fallback
        audio = obj;
    }

    /* Show Preview */
    var div = $('<div class="padding" />');
    div.append('<h1>Audio Preview</h1>');
    div.append(audio);
    $("#filesbody").append(div);
}

/* Enable or disable actions1 moreactions actions. Takes either a single
 * name, or an array of them.*/
function set_action_state(names, which, allow_on_revision)
{
    if (!(names instanceof Array)) names = Array(names);

    for (var i=0; i < names.length; i++)
    {
        element = document.getElementById('act_' + names[i]);
        if (which &&
            !(current_file.svnstatus == 'revision' && !allow_on_revision))
        {
            /* Enabling */
            element.setAttribute("class", "choice");
            element.removeAttribute("disabled");
        }
        else
        {
            /* Disabling */
            element.setAttribute("class", "disabled");
            element.setAttribute("disabled", "disabled");
        }
    }
}

/* Updates the list of available actions based on files selected */
function update_actions()
{
    var file;
    var numsel = selected_files.length;
    var svn_selection = false;
    
    if (numsel > 0)
    {
        svn_selection = true;
        for (var i = 0; i < selected_files.length; i++){
            if (!svnstatus_versioned(file_listing[selected_files[i]].svnstatus))
            {
                svn_selection = false;
            }
        }
    }
    
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
        open.setAttribute("href", build_revision_url(current_path, filename,
                                                     current_revision));
    }
    else
    {
        open.setAttribute("class", "disabled");
        open.removeAttribute("title");
        open.removeAttribute("href");
    }

    /* Serve */
    /* Available if zero or one files are selected,
     * and only if this is a file, not a directory */
    var serve = document.getElementById("act_serve");
    if (numsel <= 1 && !file.isdir && current_file.svnstatus != 'revision')
    {
        serve.setAttribute("class", "choice");
        serve.setAttribute("onclick",
              "return maybe_save('The last saved version will be served.')");
        if (numsel == 0)
            serve.setAttribute("href",
                app_url(serve_app, current_path));
        else
            serve.setAttribute("href",
                app_url(serve_app, current_path, filename));
    }
    else
    {
        serve.setAttribute("class", "disabled");
        serve.removeAttribute("href");
        serve.removeAttribute("onclick");
    }

    /* Run */
    /* Available if exactly one file is selected,
     * and it is a Python file.
     */
    var run = document.getElementById("act_run");
     
    if (numsel <= 1 && !file.isdir && file.type == "text/x-python" 
            && current_file.svnstatus != 'revision')
    {
        if (numsel == 0)
        {
            // In the edit window
            var localpath = path_join('/home', current_path);
        }
        else
        {
            // In the browser window
            var localpath = path_join('/home', current_path, filename);
        }
        run.setAttribute("class", "choice");
        run.setAttribute("onclick", "runfile('" + localpath + "')");
    }
    else
    {
        run.setAttribute("class", "disabled");
        run.removeAttribute("onclick");
    }

    /* Download */
    /* Always available for current files.
     * If 0 files selected, download the current file or directory as a ZIP.
     * If 1 directory selected, download it as a ZIP.
     * If 1 non-directory selected, download it.
     * If >1 files selected, download them all as a ZIP.
     */
    var download = document.getElementById("act_download");
    if (current_file.svnstatus == 'revision')
    {
        download.setAttribute("class", "disabled");
        download.removeAttribute("onclick");
    }
    else if (numsel <= 1)
    {
        download.setAttribute("class", "choice")
        if (numsel == 0)
        {
            download.setAttribute("href",
                app_url(download_app, current_path));
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
                app_url(download_app, current_path, filename));
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
        var dlpath = app_url(download_app, current_path) + "?";
        for (var i=0; i<numsel; i++)
            dlpath += "path=" + encodeURIComponent(selected_files[i]) + "&";
        dlpath = dlpath.substr(0, dlpath.length-1);
        download.setAttribute("class", "choice")
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
    var pubcond = numsel <= 1 && file.isdir;
    if (pubcond)
    {
        /* If this dir is already published, call it "Unpublish" */
        if (file.published)
        {
            publish.setAttribute("value", "unpublish");
            publish.setAttribute("title" ,"Make it so this directory "
                + "can not be seen by anyone on the web");
            publish.firstChild.nodeValue = "Unpublish";
        } else {
            publish.setAttribute("value", "publish");
            publish.setAttribute("title","Make it so this directory "
                + "can be seen by anyone on the web");
            publish.firstChild.nodeValue = "Publish";
        }
    }
    set_action_state(["publish", "submit"], pubcond);

    /* Share */
    /* If exactly 1 non-directory file is selected, and its parent
     * directory is published.
     */
    set_action_state("share", numsel == 1 && !file.isdir &&
                     current_file.published);

    /* Rename */
    /* If exactly 1 file is selected */
    set_action_state("rename", numsel == 1);

    /* Delete, cut, copy */
    /* If >= 1 file is selected */
    set_action_state(["delete", "cut", "copy"], numsel >= 1);

    /* Paste, new file, new directory, upload */
    /* Disable if the current file is not a directory */
    set_action_state(["paste", "newfile", "mkdir", "upload"], current_file.isdir);

    /* Subversion actions */
    /* These are only useful if we are in a versioned directory and have some
     * files selected. */
    set_action_state(["svnadd"], numsel >= 1 && current_file.svnstatus);
    /* And these are only useful is ALL the selected files are versioned */
    set_action_state(["svnremove", "svnrevert", "svncopy", "svncut"],
            numsel >= 1 && current_file.svnstatus && svn_selection);
    /* Commit is useful if ALL selected files are versioned, or the current
     * directory is versioned */
    set_action_state(["svncommit"], current_file.svnstatus &&
            (numsel >= 1 && svn_selection || numsel == 0));

    /* Diff, log and update only support one path at the moment, so we must
     * have 0 or 1 versioned files selected. If 0, the directory must be
     * versioned. */
    single_versioned_path = (
         (
          (numsel == 1 && (svnst = file_listing[selected_files[0]].svnstatus)) ||
          (numsel == 0 && (svnst = current_file.svnstatus))
         ) && svnstatus_versioned(svnst));
    set_action_state(["svndiff", "svnupdate"], single_versioned_path);

    /* We can resolve if we have a file selected and it is conflicted. */
    set_action_state("svnresolved", single_versioned_path && numsel == 1 && svnst == "conflicted");

    /* Log should be available for revisions as well. */
    set_action_state("svnlog", single_versioned_path, true);

    /* Cleanup should be available for revisions as well. */
    set_action_state("svncleanup", single_versioned_path, true);

    single_ivle_versioned_path = (
         (
          (numsel == 1 && (stat = file_listing[selected_files[0]])) ||
          (numsel == 0 && (stat = current_file))
         ) && svnstatus_versioned(stat.svnstatus)
           && stat.svnurl
           && stat.svnurl.substr(0, svn_base.length) == svn_base);
    set_action_state(["submit"], single_ivle_versioned_path);

    /* There is currently nothing on the More Actions menu of use
     * when the current file is not a directory. Hence, just remove
     * it entirely.
     * (This makes some of the above decisions somewhat redundant).
     * We also take this opportunity to show the appropriate actions2
     * bar for this path. It should either be a save or upload widget.
     */
    if (current_file.isdir)
    {
        var actions2_directory = document.getElementById("actions2_directory");
        actions2_directory.setAttribute("style", "display: inline;");
        var moreactions = document.getElementById("moreactions_area");
        moreactions.setAttribute("style", "display: inline;");
    }

    return;
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

    /* If 0 files selected, filename is the name of the current dir.
     * If 1 file selected, filename is that file.
     */
    if (selected_files.length == 0)
        filename = path_basename(current_path);
    else if (selected_files.length == 1)
        filename = selected_files[0];
    else
        filename = null;

    /* Now handle the selected action */
    switch(selectedaction)
    {
    case "publish":
        action_publish(selected_files);
        break;
    case "unpublish":
        action_unpublish(selected_files);
        break;
    case "share":
        window.open(public_app_url("~" + current_path, filename), 'share')
        break;
    case "submit":
        if (selected_files.length == 1)
            stat = file_listing[selected_files[0]];
        else
            stat = current_file;
        url = stat.svnurl.substr(svn_base.length);      // URL-encoded
        path = decodeURIComponent(url);

        /* The working copy might not have an up-to-date version of the
         * directory. While submitting like this could yield unexpected
         * results, we should really submit the latest revision to minimise
         * terrible mistakes - so we run off and ask fileservice for the
         * latest revision.*/
        $.post(app_path(service_app, current_path),
            {"action": "svnrepostat", "path": path},
            function(result)
            {
                window.location = path_join(app_path('+submit'), url) + '?revision=' + result.svnrevision;
            },
            "json");

        break;
    case "rename":
        action_rename(filename);
        break;
    case "delete":
        action_delete(selected_files);
        break;
    case "copy":
        action_copy(selected_files);
        break;
    case "cut":
        action_cut(selected_files);
        break;
    case "paste":
        action_paste();
        break;
    case "newfile":
        action_newfile();
        break;
    case "mkdir":
        action_mkdir();
        break;
    case "upload":
        show_uploadpanel(true);
        break;
    case "svnadd":
        action_add(selected_files);
        break;
    case "svnremove":
        action_remove(selected_files);
        break;
    case "svnrevert":
        action_revert(selected_files);
        break;
    case "svndiff":
        window.location = path_join(app_url('diff'), current_path, selected_files[0] || '');
        break;
    case "svnupdate":
        action_update(selected_files);
        break;
    case "svnresolved":
        action_resolved(selected_files);
        break;
    case "svncommit":
        action_commit(selected_files);
        break;
    case "svnlog":
        window.location = path_join(app_url('svnlog'), current_path, selected_files[0] || '');
        break;
    case "svncopy":
        action_svncopy(selected_files);
        break;
    case "svncut":
        action_svncut(selected_files);
        break;
    case "svncleanup":
        action_svncleanup(".");
        break;
    }
}

/** User clicks "Run" button.
 * Do an Ajax call and print the test output.
 */
function runfile(localpath)
{
    if (!maybe_save('The last saved version will be run.')) return false;

    /* Dump the entire file to the console */
    var callback = function()
    {
        console_enter_line("execfile('" + localpath + "')", "block");
    }
    start_server(callback)
    return;
}

/** Called when the page loads initially.
 */
function browser_init()
{
    /* Navigate (internally) to the path in the URL bar.
     * This causes the page to be populated with whatever is at that address,
     * whether it be a directory or a file.
     */
    var path = get_path();
    navigate(path);
}

/** Gets the current path of the window */
function get_path() {
    var path = parse_url(window.location.href).path;
    /* Strip out root_dir + "/files" from the front of the path */
    var strip = make_path(this_app);
    if (path.substr(0, strip.length) == strip)
        path = path.substr(strip.length+1);
    else
    {
        /* See if this is an edit path */
        strip = make_path(edit_app);
        if (path.substr(0, strip.length) == strip)
        {
            path = path.substr(strip.length+1);
        }
    }

    if (path.length == 0)
    {
        /* Navigate to the user's home directory by default */
        /* TEMP? */
        path = username;
    }

    return path;
}
