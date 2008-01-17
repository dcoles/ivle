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
 * Module: Listing (File Browser, client)
 * Author: Matt Giuca
 * Date: 13/1/2008
 *
 * Handles directory listings on the client side.
 */

/* Note: The DOM "tr" nodes of the file listing have extra attributes added
 * to them:
 *  filename: String.
 *  fileinfo: The file object as returned by the server.
 */

/* DOM nodeType constants */
ELEMENT_NODE = 1;

/** Filenames of all files selected */
selected_files = [];

/** The listing object returned by the server as JSON */
file_listing = null;
thisdir = null;

/** The current sort order (a list of fields to sort by, in order of
 * priority), and whether it is ascending or descending. */
sort_order = [];
sort_ascending = true;

/** The width/height of filetype, svnstatus and publishstatus icons */
icon_size = 16;

/** ACTIONS **/

function action_rename(fromfilename)
{
    var tofilename = prompt("Rename file \"" + fromfilename + "\" to?");
    if (tofilename == null) return;
    do_action("move", current_path, {"from":fromfilename, "to":tofilename});
    return false;
}

function action_remove(files)
{
    do_action("remove", current_path, {"path":files});
    return false;
}

function action_copy(files)
{
    do_action("copy", current_path, {"path":files});
    return false;
}

function action_cut(files)
{
    do_action("cut", current_path, {"path":files});
    return false;
}

function action_paste()
{
    do_action("paste", current_path, {"path":"."});
    return false;
}

function action_add(files)
{
    do_action("svnadd", current_path, {"path":files});
    return false;
}

function action_revert(files)
{
    do_action("svnrevert", current_path, {"path":files});
    return false;
}

function action_commit(files)
{
    /* Get a commit log from the user */
    var logmsg = prompt("Enter commit log:");
    if (logmsg == null) return;
    do_action("svncommit", current_path, {"path":files, "logmsg": logmsg});
    return false;
}

/** END ACTIONS **/

/** Updates the side-panel. Expects selected_files reflects the current
 * selected files.
 */
function update_sidepanel(total_file_size_sel)
{
    var sidepanel = document.getElementById("sidepanel");
    var filename;
    var file;
    var p;
    /* Is this dir under svn? */
    var under_subversion = "svnstatus" in thisdir;
    dom_removechildren(sidepanel);
    if (selected_files.length <= 1)
    {
        if (selected_files.length == 0)
        {
            /* Display information about the current directory instead */
            filename = path_basename(current_path);
            file = thisdir;
        }
        else if (selected_files.length == 1)
        {
            filename = selected_files[0];
            file = file_listing[filename];
        }
        var filetype;
        if ("isdir" in file && file.isdir)
            filetype = "text/directory";
        else if ("type" in file)
            filetype = file.type;
        else
            filetype = "text/plain";

        if ("type_nice" in file)
            filetype_nice = file.type_nice;
        else
            filetype_nice = "File";

        p = document.createElement("p");
        sidepanel.appendChild(p);
        p.appendChild(dom_make_img(mime_type_to_icon(filetype, true),
            null, null, filetype));
        p = dom_make_text_elem("h2", filename);
        sidepanel.appendChild(p);
        p = dom_make_text_elem("p", filetype_nice);
        sidepanel.appendChild(p);
        if (under_subversion)
        {
            p = document.createElement("p");
            var icon = svnstatus_to_icon(file.svnstatus);
            if (icon)
                p.appendChild(dom_make_img(icon, icon_size, icon_size,
                    svnstatus_to_string(file.svnstatus)));
            sidepanel.appendChild(p);
            p = dom_make_text_elem("p", svnstatus_to_string(file.svnstatus));
            sidepanel.appendChild(p);
        }
        if ("size" in file)
        {
            p = dom_make_text_elem("p", "Size: " + nice_filesize(file.size));
            sidepanel.appendChild(p);
        }
        if ("mtime_nice" in file)
        {
            p = dom_make_text_elem("p", "Modified: " + file.mtime_nice);
            sidepanel.appendChild(p);
        }
    }
    else
    {
        /* Multiple files selected */
        p = document.createElement("p");
        sidepanel.appendChild(p);
        p.appendChild(dom_make_img(
            app_path(type_icons_path_large, "multi.png"),
            null, null, "Multiple files"));
        p = dom_make_text_elem("h2",
            selected_files.length.toString() + " files selected");
        sidepanel.appendChild(p);
        p = dom_make_text_elem("p", "Total size: "
            + nice_filesize(total_file_size_sel));
        sidepanel.appendChild(p);
    }

    p = dom_make_text_elem("h3", "Actions");
    sidepanel.appendChild(p);

    if (selected_files.length <= 1)
    {
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
        path = app_path(download_app, current_path, filename);
        if (file.isdir)
            p = dom_make_link_elem("p", "Download as zip",
                "Download this directory as a ZIP file", path);
        else
            p = dom_make_link_elem("p", "Download",
                "Download this file to your computer", path);
        if (p)
            sidepanel.appendChild(p);

        p = dom_make_link_elem("p", "Rename",
            "Change the name of this file", null,
            "return action_rename(" + repr(filename) + ")");
        sidepanel.appendChild(p);
    }
    else
    {
        path = app_path(download_app, current_path) + "?";
        for (var i=0; i<selected_files.length; i++)
            path += "path=" + encodeURIComponent(selected_files[i]) + "&";
        path = path.substr(0, path.length-1);
        /* Multiple files selected */
        p = dom_make_link_elem("p", "Download as zip",
            "Download the selected files as a ZIP file", path);
        sidepanel.appendChild(p);
    }

    /* Common actions */
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
    p = dom_make_link_elem("p", "Paste",
        "Paste the copied or cut files to the current directory", null,
        "return action_paste()");
    sidepanel.appendChild(p);

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

/** Updates the side-panel and status bar to reflect the current set of
 * selected files. This is done by inspecting the states of the check boxes.
 * Also changes the styling to highlight selected files.
 */
function update_selection()
{
    /* First get a list of all files that are selected, and
     * reset the styling on each file's row. */
    var files_children = document.getElementById("files").childNodes;
    var tr;
    var checkbox;
    var row_toggle = 1;
    selected_files = [];  /* Clear global selected_files */

    var total_file_size = 0;    /* In bytes */
    var total_file_size_sel = 0;

    /* Children are trs */
    var filename;
    var file;
    if (file_listing == null) return;
    for (var i=0; i<files_children.length; i++)
    {
        filename = files_children[i].filename;
        file = files_children[i].fileinfo;
        /* Count total file size so we can write to the status bar later
         */
        if ("size" in file)
            total_file_size += file.size;

        tr = files_children[i];
        checked = tr.firstChild.firstChild.checked;
        /* Set the class for every row based on both the checked state,
         * and whether it is odd or even */
        tr.setAttribute("class", "row" + row_toggle.toString() +
            (checked ? "sel" : ""))
        row_toggle = row_toggle == 1 ? 2 : 1;
        if (checked)
        {
            /* Add the filename (column 3) to the selected_files list */
            selected_files[selected_files.length] = filename;
            if ("size" in file)
                total_file_size_sel += file.size;
        }
    }

    /* Write to the side-panel */
    update_sidepanel(total_file_size_sel);

    /* Write to the status bar */
    var statusbar = document.getElementById("statusbar");
    var statusmsg;
    var file_plural;
    if (selected_files.length > 0)
    {
        statusmsg = selected_files.length.toString() + " file"
            + (selected_files.length == 1 ? "" : "s") + " selected, "
            + nice_filesize(total_file_size_sel);
    }
    else
    {
        statusmsg = files_children.length.toString() + " file"
            + (files_children.length == 1 ? "" : "s") + ", "
            + nice_filesize(total_file_size);
    }
    dom_removechildren(statusbar);
    statusbar.appendChild(document.createTextNode(statusmsg));
}

/** SORTING FUNCTIONS **/

/** Sorts the file table. Physically manipulates the DOM table to reflect the
 * sorted nodes, and also updates the little sort arrow.
 *
 * \param sort_field The name of the field to sort on primarily. This can
 * either be "filename", or one of the fields of a fileinfo object. Note that
 * while this determines the primary sort key, the secondary sort keys are
 * determined by the global sort_order. Calling sort_listing reorders
 * sort_order, bringing the specified sort_field to the top.
 * Also note that sorting by "isdir" is more prominent than whatever field is
 * provided here.
 * \param ascending If true, sorts ascending. If false, descending.
 */
function sort_listing(sort_field, ascending)
{
    var i;
    var files = document.getElementById("files");
    var files_children = files.childNodes;
    var files_array = new Array(files_children.length);
    /* Update sort_order, bringing sort_field to the top. */
    sort_order.removeall(sort_field);
    sort_order.push(sort_field);
    sort_ascending = ascending != false ? true : false;

    /* Build an array of DOM tr elements (with the additional 'filename' and
     * 'fileinfo' attributes as written when the listing is created). */
    /* Note: Must manually create an array from files_children, which is a DOM
     * NodeList, not an array. */
    for (i=0; i<files_children.length; i++)
        files_array[i] = files_children[i];

    /* Sort this array */
    files_array.sort(compare_files);

    /* Clean out the table (the TRs are safely stored in the array) */
    dom_removechildren(files);

    /* Insert the TRs back into the table, in their sorted order */
    for (i=0; i<files_array.length; i++)
        files.appendChild(files_array[i]);

    /* Fix the coloring classes on the rows so they are interleaved. */
    update_selection();

    return false;
}

/** Comparison function used for sorting. Compares two DOM tr nodes (with
 * the additional 'filename' and 'fileinfo' attributes as written when the
 * listing is created).
 * Returns an integer, which is -1 if a < b, 0 if a == b, and 1 if a > b.
 * The fields to compare by are determined by the global variable sort_order.
 */
function compare_files(a, b)
{
    /* First sort by whether or not it is a directory */
    var aisdir = a.fileinfo.isdir == true;
    var bisdir = b.fileinfo.isdir == true;
    var LESS = sort_ascending == true ? -1 : 1;
    var GREATER = -LESS;
    if (aisdir > bisdir) return LESS;
    else if (aisdir < bisdir) return GREATER;

    /* Reverse order of sort_order. (top is highest priority) */
    for (var i=sort_order.length-1; i>=0; i--)
    {
        var field = sort_order[i];
        if (field == "filename")
        {
            if (a.filename < b.filename) return LESS;
            else if (a.filename > b.filename) return GREATER;
        }
        else
        {
            /* null > anything else (so it appears at the bottom) */
            if (!(field in a))
                if (field in b) return GREATER; else break;
            if (!(field in b)) return LESS;
            if (a.fileinfo[field] < b.fileinfo[field]) return LESS;
            else if (a.fileinfo[field] > b.fileinfo[field]) return GREATER;
        }
    }

    return 0;
}

/** END SORTING **/

/** Clears all selected files and causes the single file specified to become
 * selected.
 * \param filename The file in the list to select.
 */
function select_file(filename)
{
    var files_children = document.getElementById("files").childNodes;
    var checkbox;
    var tr;
    for (var i=0; i<files_children.length; i++)
    {
        tr = files_children[i];
        checkbox = tr.firstChild.firstChild;
        checkbox.checked = tr.filename == filename;
    }
    update_selection();
}

/** Initialises the DOM elements required to present a dir listing,
 * assuming that clear_page has just been called or the page just
 * loaded for the first time.
 */
function setup_for_dir_listing()
{
    var filesbody = document.getElementById("filesbody");

    /* Using a table-based layout, for reasons of sanity */
    /* One row, 2 columns */
    var middle = document.createElement("table");
    filesbody.appendChild(middle);
    middle.setAttribute("id", "middle");
    var middle_tbody = document.createElement("tbody");
    middle.appendChild(middle_tbody);
    var middle_tr = document.createElement("tr");
    middle_tbody.appendChild(middle_tr);

    /* Column 1: File table */
    var filetable = document.createElement("td");
    middle_tr.appendChild(filetable);
    filetable.setAttribute("id", "filetable");
    var filetablediv = document.createElement("div");
    filetable.appendChild(filetablediv);
    filetablediv.setAttribute("id", "filetablediv");
    /* A nested table within this div - the actual files listing */
    var filetabletable = document.createElement("table");
    filetablediv.appendChild(filetabletable);
    filetabletable.setAttribute("width", "100%");
    var filetablethead = document.createElement("thead");
    filetabletable.appendChild(filetablethead);
    var filetablethead_tr = document.createElement("tr");
    filetablethead.appendChild(filetablethead_tr);
    filetablethead_tr.setAttribute("class", "rowhead");
    /* Row headers */
    var filetablethead_th = document.createElement("th");
    filetablethead_tr.appendChild(filetablethead_th);
    filetablethead_th.setAttribute("class", "col-check");
    filetablethead_th = dom_make_link_elem("th", "Filename",
        "Sort by filename", null, "return sort_listing(\"filename\")");
    filetablethead_tr.appendChild(filetablethead_th);
    filetablethead_th.setAttribute("class", "col-filename");
    filetablethead_th.setAttribute("colspan", 3);
    filetablethead_th = dom_make_link_elem("th", "Size",
        "Sort by file size", null, "return sort_listing(\"size\")");
    filetablethead_tr.appendChild(filetablethead_th);
    filetablethead_th.setAttribute("class", "col-size");
    filetablethead_th = dom_make_link_elem("th", "Modified",
        "Sort by date modified", null, "return sort_listing(\"mtime\")");
    filetablethead_tr.appendChild(filetablethead_th);
    filetablethead_th.setAttribute("class", "col-date");
    /* Empty body */
    var filetabletbody = document.createElement("tbody");
    filetabletable.appendChild(filetabletbody);
    filetabletbody.setAttribute("id", "files");

    /* Column 2: Side-panel */
    var sidepanel = document.createElement("td");
    middle_tr.appendChild(sidepanel);
    sidepanel.setAttribute("id", "sidepanel");


    /* Now after the table "middle", there is a status bar */
    var statusbar = document.createElement("div");
    filesbody.appendChild(statusbar);
    statusbar.setAttribute("id", "statusbar");
}

/** Presents the directory listing.
 */
function handle_dir_listing(path, listing)
{
    setmode(false);
    setup_for_dir_listing();
    var row_toggle = 1;
    /* Nav through the top-level of the JSON to the actual listing object. */
    var listing = listing.listing;
    file_listing = listing;     /* Global */

    /* Get "." out, it's special */
    thisdir = listing["."];     /* Global */
    delete listing["."];
    /* Is this dir under svn? */
    var under_subversion = "svnstatus" in thisdir;

    var files = document.getElementById("files");
    var file;
    var row;
    var td;
    var checkbox;

    var selection_string;

    /* Create all of the files */
    for (var filename in listing)
    {
        selection_string = "select_file(" + repr(filename) + ")";
        file = listing[filename];
        /* Make a 'tr' element. Store the filename and fileinfo in
         * here. */
        row = document.createElement("tr");
        row.filename = filename;
        row.fileinfo = file;
        /* Column 1: Selection checkbox */
        row.setAttribute("class", "row" + row_toggle.toString())
        row_toggle = row_toggle == 1 ? 2 : 1;
        td = document.createElement("td");
        checkbox = document.createElement("input");
        checkbox.setAttribute("type", "checkbox");
        checkbox.setAttribute("title", "Select this file");
        checkbox.setAttribute("onchange", "update_selection()");
        td.appendChild(checkbox);
        row.appendChild(td);
        if (file.isdir)
        {
            /* Column 2: Filetype and subversion icons. */
            td = document.createElement("td");
            td.setAttribute("class", "thincol");
            td.setAttribute("onclick", selection_string);
            td.appendChild(dom_make_img(mime_type_to_icon("text/directory"),
                icon_size, icon_size, file.type_nice));
            row.appendChild(td);
            td = document.createElement("td");
            td.setAttribute("class", "thincol");
            if (under_subversion)
            {
                var icon = svnstatus_to_icon(file.svnstatus);
                if (icon)
                    td.appendChild(dom_make_img(icon, icon_size, icon_size,
                        svnstatus_to_string(file.svnstatus)));
            }
            row.appendChild(td);
            /* Column 3: Filename */
            td = dom_make_link_elem("td", filename,
                "Navigate to " + path_join(path, filename),
                app_path(this_app, path, filename)/*,
                "navigate(" + repr(path_join(path, filename)) + ")"*/);
            td.setAttribute("onclick", selection_string);
            row.appendChild(td);
        }
        else
        {
            /* Column 2: Filetype and subversion icons. */
            td = document.createElement("td");
            td.setAttribute("class", "thincol");
            td.appendChild(dom_make_img(mime_type_to_icon(file.type),
                icon_size, icon_size, file.type_nice));
            row.appendChild(td);
            td = document.createElement("td");
            td.setAttribute("class", "thincol");
            if (under_subversion)
            {
                var icon = svnstatus_to_icon(file.svnstatus);
                if (icon)
                    td.appendChild(dom_make_img(icon, icon_size, icon_size,
                        svnstatus_to_string(file.svnstatus)));
            }
            row.appendChild(td);
            /* Column 3: Filename */
            td = dom_make_text_elem("td", filename);
            td.setAttribute("onclick", selection_string);
            row.appendChild(td);
        }
        /* Column 4: Size */
        td = dom_make_text_elem("td", nice_filesize(file.size));
        td.setAttribute("onclick", selection_string);
        row.appendChild(td);
        /* Column 4: Date */
        td = dom_make_text_elem("td", file.mtime_short, file.mtime_nice);
        td.setAttribute("onclick", selection_string);
        row.appendChild(td);
        files.appendChild(row);
    }

    /* Apply an initial sort by filename */
    sort_listing("filename");

    /* Do a selection update (create initial elements for side panel and
     * status bar). */
    /* Commented out; already called by sort_listing */
    /*update_selection();*/
}

