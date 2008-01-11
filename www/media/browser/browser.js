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
service_app = "fileservice";

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

/* List of MIME types considered "executable" by the system.
 * Executable files offer a "run" link, implying that the "serve"
 * application can interpret them.
 */
types_exec = [
    "text/x-python",
];

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
 */
function navigate(path)
{
    /* Call the server and request the listing. This mutates the server. */
    response = ajax_call(service_app, path, null, "GET");
    /* Now read the response and set up the page accordingly */
    handle_response(path, response);
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
 */
function handle_response(path, response)
{
    /* TODO: Set location bar to "path" */
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
    if (response.getResponseHeader("X-IVLE-Return") == "Dir")
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
        var handler_type;
        if (content_type in type_handlers)
            handler_type = type_handlers[content_type];
        else
        {   /* Based on the first part of the MIME type */
            handler_type = content_type.split('/')[0];
            if (handler_type != "text" && handler_type != "image" &&
                handler_type != "audio")
                handler_type = "binary";
        }
        /* handler_type should now be set to either
         * "text", "image", "audio" or "binary". */
        switch (handler_type)
        {
        case "text":
            handle_text(path, response.responseText);
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
    /* Note: For now clear just enough to repopulate with a dir listing.
     * Later, will have to clear more to make way for other handlers.
     * Possibly have a "full clear" for all handlers, and special
     * less-violent clearers for each handler if the same handler is going to
     * be used that was used last time. */
    dom_removechildren(document.getElementById("path"));
    dom_removechildren(document.getElementById("files"));
    dom_removechildren(document.getElementById("sidepanel"));
}

/*** HANDLERS for different types of responses (such as dir listing, file,
 * etc). */

function handle_error(message)
{
    /* TODO: Find a better place to put this message. */
    var msg_elem = document.getElementById("path");
    var txt_elem = dom_make_text_elem("span", "Error: "
        + message.toString() + ".")
    txt_elem.setAttribute("class", "error");
    msg_elem.appendChild(txt_elem)
}

/** Presents a path list (address bar inside the page) for clicking.
 * (Dir listing).
 */
function presentpath(path)
{
    var dom_path = document.getElementById("path");
    var navlist = [];
    var href_path = make_path(this_app);

    /* Create all of the paths */
    for each (dir in path.split("/"))
    {
        if (dir == "") continue;
        navlist.push(dir);
        /* Make an 'a' element */
        href_path = path_join(href_path, dir);
        var link = dom_make_link_elem("a", dir, href_path,
                "navigate(" + href_path + ")");
        dom_path.appendChild(link);
        dom_path.appendChild(document.createTextNode("/"));
    }
}

/** Presents the directory listing.
 */
function handle_dir_listing(path, listing)
{
    var row_toggle = 1;
    presentpath(path);
    /* Nav through the top-level of the JSON to the actual listing object. */
    var listing = listing.listing;

    /* Get "." out, it's special */
    var thisdir = listing["."];
    delete listing["."];
    /* Is this dir under svn? */
    var under_subversion = "svnstatus" in thisdir;

    var files = document.getElementById("files");
    var file;
    var row;
    var td;
    var checkbox;

    /* Create all of the files */
    for (var filename in listing)
    {
        file = listing[filename];
        /* Make a 'tr' element */
        row = document.createElement("tr");
        /* Column 1: Selection checkbox */
        row.setAttribute("class", "row" + row_toggle.toString())
        row_toggle = row_toggle == 1 ? 2 : 1;
        td = document.createElement("td");
        checkbox = document.createElement("input");
        checkbox.setAttribute("type", "checkbox");
        checkbox.setAttribute("title", "Select this file");
        td.appendChild(checkbox);
        row.appendChild(td);
        if (file.isdir)
        {
            /* Column 2: Filetype and subversion icons. */
            td = document.createElement("td");
            td.setAttribute("class", "thincol");
            td.appendChild(document.createTextNode("dir"));
            row.appendChild(td);
            td = document.createElement("td");
            td.setAttribute("class", "thincol");
            if (under_subversion)
                td.appendChild(document.createTextNode(file.svnstatus));
            row.appendChild(td);
            /* Column 3: Filename */
            row.appendChild(dom_make_link_elem("td", filename,
                make_path(path_join(this_app, path, filename)),
                "navigate(" + path_join(path, filename) + ")"));
        }
        else
        {
            /* Column 2: Filetype and subversion icons. */
            td = document.createElement("td");
            td.setAttribute("class", "thincol");
            td.appendChild(document.createTextNode(file.type));
            row.appendChild(td);
            td = document.createElement("td");
            td.setAttribute("class", "thincol");
            if (under_subversion)
                td.appendChild(document.createTextNode(file.svnstatus));
            row.appendChild(td);
            /* Column 3: Filename */
            row.appendChild(dom_make_text_elem("td", filename));
        }
        /* Column 4: Size */
        row.appendChild(dom_make_text_elem("td", nice_filesize(file.size)));
        /* Column 4: Date */
        row.appendChild(dom_make_text_elem("td", file.mtime_nice));
        files.appendChild(row);
    }

}

/** Presents the text editor.
 */
function handle_text(path, text)
{
    /* TODO */
    alert(text);
}

/** Displays a download link to the binary file.
 */
function handle_binary(path)
{
    /* TODO */
    alert(path);
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
    strip_chars = make_path(this_app).length + 1;
    path = path.substr(strip_chars);

    navigate(path);
}
