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

/* DOM nodeType constants */
ELEMENT_NODE = 1;

/** Filenames of all files selected */
selected_files = [];

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
    /* Children are trs */
    for (var i=0; i<files_children.length; i++)
    {
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
            filename = tr.childNodes[3].firstChild;
            if (filename.nodeType == ELEMENT_NODE)
                filename = filename.firstChild.data;
            else
                filename = filename.data;
            selected_files[selected_files.length] = filename;
        }
    }
}

/** Clears all selected files and causes the single file specified to become
 * selected.
 * \param fileid The index of the file in the list to select.
 */
function select_file(fileid)
{
    var files_children = document.getElementById("files").childNodes;
    var checkbox;
    for (var i=0; i<files_children.length; i++)
    {
        tr = files_children[i];
        checkbox = tr.firstChild.firstChild;
        checkbox.checked = i == fileid;
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
        "Sort by filename", "")
    filetablethead_tr.appendChild(filetablethead_th);
    filetablethead_th.setAttribute("class", "col-filename");
    filetablethead_th.setAttribute("colspan", 3);
    filetablethead_th = dom_make_link_elem("th", "Size",
        "Sort by file size", "")
    filetablethead_tr.appendChild(filetablethead_th);
    filetablethead_th.setAttribute("class", "col-size");
    filetablethead_th = dom_make_link_elem("th", "Modified",
        "Sort by date modified", "")
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
    var i;
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

    var total_files = 0;
    var total_file_size = 0;    /* In bytes */

    var selection_string;

    /* Create all of the files */
    i = 0;
    for (var filename in listing)
    {
        selection_string = "select_file(" + i.toString() + ")";
        file = listing[filename];
        total_files++;
        if ("size" in file)
            total_file_size += file.size;
        /* Make a 'tr' element */
        row = document.createElement("tr");
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
                22, 22, file.type));
            row.appendChild(td);
            td = document.createElement("td");
            td.setAttribute("class", "thincol");
            if (under_subversion)
                td.appendChild(dom_make_img(svnstatus_to_icon(file.svnstatus),
                    22, 22, file.svnstatus));
            row.appendChild(td);
            /* Column 3: Filename */
            td = dom_make_link_elem("td", filename,
                "Navigate to " + path_join(path, filename),
                make_path(path_join(this_app, path, filename)),
                "navigate(" + path_join(path, filename) + ")");
            td.setAttribute("onclick", selection_string);
            row.appendChild(td);
        }
        else
        {
            /* Column 2: Filetype and subversion icons. */
            td = document.createElement("td");
            td.setAttribute("class", "thincol");
            td.appendChild(dom_make_img(mime_type_to_icon(file.type),
                22, 22, file.type));
            row.appendChild(td);
            td = document.createElement("td");
            td.setAttribute("class", "thincol");
            if (under_subversion)
                td.appendChild(dom_make_img(svnstatus_to_icon(file.svnstatus),
                    22, 22, file.svnstatus));
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
        i++;
    }

    /* Write to the status bar */
    var statusbar = document.getElementById("statusbar");
    var statusmsg = total_files.toString() + " files, "
        + nice_filesize(total_file_size);
    dom_removechildren(statusbar);
    statusbar.appendChild(document.createTextNode(statusmsg));
}

