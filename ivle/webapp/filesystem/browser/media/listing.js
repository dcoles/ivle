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

/** The current sort order (a list of fields to sort by, in order of
 * priority), and whether it is ascending or descending. */
sort_order = [];
sort_ascending = true;

/** The width/height of filetype, svnstatus and publishstatus icons */
icon_size = 16;

/** ACTIONS **/

/** Do a action on the current path and then run the handle_response callback 
 **/
function do_act(action, args) {
    do_action(action, current_path, args, null,
            function(path, response) {
                handle_response(path, response, true);
            });
}

function action_rename(fromfilename)
{
    var tofilename = prompt("Rename file \"" + fromfilename + "\" to?",
        fromfilename);
    if (tofilename == null) return;
    do_act("move", {"from":fromfilename, "to":tofilename});
    return false;
}

function action_delete(files)
{
    var conf_msg;
    /* A heavy nesty bit of logic to determine the confirmation message.
     */
    if (files.length == 0)
        return;
    else if (files.length == 1)
    {
        if (file_listing[files[0]].isdir)
            conf_msg = "Are you sure you want to delete the directory \""
                + files[0] + "\"?\n"
                + "All of the files in this directory will be lost.";
        else
            conf_msg = "Are you sure you want to delete the file \""
                + files[0] + "\"?";
    }
    else
    {
        var confirm_filelist = "";
        var num_dirs = 0;
        for (var i=0; i<files.length; i++)
        {
            if (file_listing[files[i]].isdir)
                num_dirs++;
            confirm_filelist += "  - " + files[i] + "\n";
        }
        conf_msg = "Are you sure you want to delete all of the "
            + "following ";
        if (num_dirs > 0)
        {
            if (files.length == num_dirs)
                conf_msg += "directories";
            else
                conf_msg += "files and directories";
        }
        else
            conf_msg += "files";
        conf_msg += ":\n" + confirm_filelist;
        if (num_dirs > 0)
            conf_msg += "\nAll of the files in these directories "
                     + "will be lost.";
    }
    /* Now we have the conf message */

    var confirmed = confirm(conf_msg);
    if (!confirmed) return;
    do_act("delete", {"path":files});
    return false;
}

function action_mkdir()
{
    var path = prompt("New directory name?","");
    if (path == null) return;
    do_act("mkdir", {"path":path});
    return false;
}

function action_newfile()
{
    var path = prompt("New file name?","");
    if (path == null) return;
    /* "Upload" a blank file */
    /* Note: "overwrite" defaults to false, so will error if it already
     * exists. */
    do_act("putfile", {"path":path, "data":""});
    return false;
}

/* Mode is either "copy" or "move".
 */
function action_copy_or_cut(files, mode)
{
    /* Store the "clipboard" in the browser cookie */
    var clip_obj = {"src": current_path, "file": files, "mode": mode};
    write_cookie("clipboard", clip_obj);
}

function action_copy(files)
{
    action_copy_or_cut(files, "copy");
    return false;
}

function action_cut(files)
{
    action_copy_or_cut(files, "move");
    return false;
}

function action_paste()
{
    /* Get the "clipboard" object from the browser cookie */
    var clip_obj = read_cookie("clipboard");
    var under_subversion;
    
    if (clip_obj == null)
    {
        alert("No files have been cut or copied.");
        return false;
    }

    if (clip_obj.mode == "svnmove" || clip_obj.mode == "svncopy")
    {
        under_subversion = ("svnstatus" in current_file) &&
                                (svnstatus_versioned(current_file.svnstatus));
        if (!under_subversion)
        {
            alert("Cannot perform an Subversion Move outside of"
                                                + " Permanent directories!");
            return false;
        }        
    }
    
    /* The clip_obj is exactly what we want to pass, plus the current path
     * as destination. */
    clip_obj.dst = ".";
    do_act("paste", clip_obj);
    return false;
}

function action_svncopy(files)
{
    action_copy_or_cut(files, "svncopy");
    return false;
}

function action_svncut(files)
{
    action_copy_or_cut(files, "svnmove");
    return false;
}

function action_add(files)
{
    do_act("svnadd", {"path":files});
    return false;
}

function action_remove(files)
{
    do_act("svnremove", {"path":files});
    return false;
}

function action_revert(files)
{
    do_act("svnrevert", {"path":files});
    return false;
}

function action_publish(files)
{
    do_act("publish", {"path":files});
    return false;
}

function action_unpublish(files)
{
    do_act("unpublish", {"path":files});
    return false;
}

function action_update(files)
{
    if (files.length == 0) files = ".";
    do_act("svnupdate", {"path": files});
    return false;
}

function action_resolved(files)
{
    if (files.length == 0) files = ".";
    do_act("svnresolved", {"path": files});
    return false;
}

function action_commit(files)
{
    /* Get a commit log from the user */
    var logmsg = prompt("Enter commit log:","");
    if (logmsg == null) return;
    do_act("svncommit", {"path":files, "logmsg": logmsg});
    return false;
}

function action_svncleanup(path)
{
    do_act("svncleanup", {"path": path});
    alert("Subversion Cleanup Complete");
}

/** Selects or deselects all files in the listing.
 * selected: true or false (defaults to true).
 * If false, deselects instead of selecting.
 */
function action_selectall(selected)
{
    if (selected == null)
        selected = true;
    /* Iterate through and check all the boxes.
     * Then update.
     * (We do this through the DOM because that is the authority that
     * update_selection uses to identify what is selected).
     */
    var files_children = document.getElementById("files").childNodes;
    for (var i=0; i<files_children.length; i++)
    {
        tr = files_children[i];
        tr.firstChild.firstChild.checked = selected;
    }
    update_selection();
}

/* Shows or hides the "upload panel" in the side panel.
 * toshow is true for showing, false for hiding.
 */
uploadpanel_shown = false;
function show_uploadpanel(toshow)
{
    if (toshow == null)
        uploadpanel_shown = !uploadpanel_shown;
    else
        uploadpanel_shown = toshow;
    document.getElementById("uploadpanel").setAttribute("style",
        "display: " + (uploadpanel_shown ? "auto" : "none") + ";");
    return false;
}

/** END ACTIONS **/

/** Updates the side-panel AND the actions in the top-bar. Expects selected_files
 * reflects the current selected files.
 */
function update_sidepanel(total_file_size_sel)
{
    var sidepanel = document.getElementById("sidepanel");
    var filename;
    var file;
    var p;
    var div;
    /* Is this dir under svn? */
    var under_subversion = "svnstatus" in current_file;
    dom_removechildren(sidepanel);
    if (selected_files.length <= 1)
    {
        if (selected_files.length == 0)
        {
            /* Display information about the current directory instead */
            filename = path_basename(current_path);
            file = current_file;
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
        var mini_icons = document.createElement("p");
        sidepanel.appendChild(mini_icons);
        var icon;
        if (under_subversion)
        {
            icon = svnstatus_to_icon(file.svnstatus);
            if (icon)
                mini_icons.appendChild(dom_make_img(icon, icon_size, icon_size,
                    svnstatus_to_string(file.svnstatus)));
            p = dom_make_text_elem("p", svnstatus_to_string(file.svnstatus));
            sidepanel.appendChild(p);
        }
        if ("published" in file && file.published)
        {
            icon = make_path(path_join(published_icon));
            if (icon)
            {
                if (mini_icons.childNodes.length > 0)
                    mini_icons.appendChild(document.createTextNode(" "));
                mini_icons.appendChild(dom_make_img(icon, icon_size, icon_size,
                    "Published to the web"));
            }
            p = dom_make_text_elem("p", "Published to the web");
            p.setAttribute("title",
                "Anybody on the web can view the files in this directory.");
            sidepanel.appendChild(p);
        }
        /* If we never wrote any mini-icons, remove this element */
        if (mini_icons.childNodes.length == 0)
            sidepanel.removeChild(mini_icons);
        if ("size" in file)
        {
            p = dom_make_text_elem("p", "Size: " + nice_filesize(file.size));
            sidepanel.appendChild(p);
        }
        if ("mtime_nice" in file)
        {
            /* Break into lines on comma (separating date from time) */
            filetime_lines = file.mtime_nice.split(",");
            p = document.createElement("p");
            p.appendChild(document.createTextNode("Modified:"));
            for (var i=0; i<filetime_lines.length; i++)
            {
                p.appendChild(document.createElement("br"));
                p.appendChild(document.createTextNode(filetime_lines[i]));
            }
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

    /* Write to the side-panel and actions bar */
    update_actions();
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
    if(sort_order[sort_order.length-1] == sort_field)
    {
        sort_ascending = ascending != false ? true : false;
    }
    else
    {
        sort_ascending = true;
        sort_order.removeall(sort_field);
        sort_order.push(sort_field);
    }

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
            if (!(field in a.fileinfo))
            {
                if (field in b.fileinfo)
                    return GREATER;
                else
                    break;
            }
            if (!(field in b.fileinfo)) return LESS;
            if (a.fileinfo[field] < b.fileinfo[field]) return LESS;
            else if (a.fileinfo[field] > b.fileinfo[field]) return GREATER;
        }
    }

    return 0;
}

/** END SORTING **/

/** Initialises the DOM elements required to present files window,
 * assuming that clear_page has just been called or the page just
 * loaded for the first time.
 */
function setup_for_listing()
{
    var filesbody = document.getElementById("filesbody");

    /* There are 2 divs in the filesbody: middle and statusbar
     * middle has 2 divs: filetable, sidepanel
     */
    /* Middle */
    var middle = document.createElement("div");
    filesbody.appendChild(middle);
    middle.setAttribute("id", "middle");
    /* File table */
    var filetable = document.createElement("div");
    middle.appendChild(filetable);
    filetable.setAttribute("id", "filetable");
    var filetablediv = document.createElement("div");
    filetable.appendChild(filetablediv);
    filetablediv.setAttribute("id", "filetablediv");

    /* Side-panel */
    /* 2 nested divs, so we can set the width exactly and have padding inside
     * of that */
    var sidepanel_outer = document.createElement("div");
    middle.appendChild(sidepanel_outer);
    sidepanel_outer.setAttribute("id", "sidepanel_outer");
    var sidepanel = document.createElement("div");
    sidepanel_outer.appendChild(sidepanel);
    sidepanel.setAttribute("id", "sidepanel");

    /* Now after the table "middle", there is a status bar */
    var statusbar_outer = document.createElement("div");
    filesbody.appendChild(statusbar_outer);
    statusbar_outer.setAttribute("id", "statusbar_outer");
    var statusbar = document.createElement("div");
    statusbar_outer.appendChild(statusbar);
    statusbar.setAttribute("id", "statusbar");
}

/** Sets up the DOM elements required to present a directory liisting.
 */
function setup_dir_listing()
{
    var filesbody = document.getElementById("filesbody");
    var filetable = document.getElementById("filetable");
    var filetablediv = document.getElementById("filetablediv");

    /* A nested table within this div - the actual files listing */
    var filetabletable = document.createElement("table");
    filetablediv.appendChild(filetabletable);
    filetabletable.setAttribute("width", "100%");

    $('\
<thead> \
  <tr class="rowhead"> \
    <th class="col-check"> \
      <input title="Select All" onclick="action_selectall(this.checked)" type="checkbox"> \
    </th> \
    <th colspan="3" class="col-filename"> \
      <a onclick="return sort_listing(\'filename\', !sort_ascending)" title="Sort by filename" href="">Filename</a> \
    </th> \
    <th class="col-size"> \
      <a onclick="return sort_listing(\'size\', !sort_ascending)" title="Sort by file size" href="">Size</a> \
    </th> \
    <th class="col-date"> \
      <a onclick="return sort_listing(\'mtime\', !sort_ascending)" title="Sort by date modified" href="">Modified</a> \
    </th> \
  </tr> \
</thead>').appendTo(filetabletable);

    /* Empty body */
    var filetabletbody = document.createElement("tbody");
    filetabletable.appendChild(filetabletbody);
    filetabletbody.setAttribute("id", "files");
}

/** Presents the directory listing.
 */
function handle_dir_listing(path, listing)
{
    /* Add the DOM elements for the file listing */
    setup_dir_listing()

    var row_toggle = 1;
    
    /* Is this dir under svn? */
    var under_subversion = ("svnstatus" in current_file) &&
            (svnstatus_versioned(current_file.svnstatus));

    var files = document.getElementById("files");
    var file;
    var row;
    var td;
    var checkbox;

    /* Convert selected_files array into a dictionary which can be efficiently
     * searched. */
    sel_files_dict = {};
    for (var i=0; i<selected_files.length; i++)
    {
        sel_files_dict[selected_files[i]] = true;
    }

    /* Create all of the files */
    for (var filename in listing)
    {
        select_row = function() {
            var files_children = document.getElementById("files").childNodes;
            var checkbox;
            var tr;
            for (var i=0; i<files_children.length; i++)
            {
                tr = files_children[i];
                checkbox = tr.firstChild.firstChild;
                checkbox.checked = tr == this.parentNode;
            }
            update_selection();
        }

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
        checkbox.setAttribute("onclick", "update_selection()");
        /* Check the box if selected_files says it's selected */
        checkbox.checked = filename in sel_files_dict;
        td.appendChild(checkbox);
        row.appendChild(td);

        /* Column 2: Filetype and subversion icons. */
        td = document.createElement("td");
        td.setAttribute("class", "thincol");
        $(td).click(select_row);
        /* Directories don't really have a MIME type, so we fake one. */
        if (file.isdir) file.type = "text/directory";
        td.appendChild(dom_make_img(mime_type_to_icon(file.type),
            icon_size, icon_size, file.type_nice));
        row.appendChild(td);
        td = document.createElement("td");
        td.setAttribute("class", "thincol");
        var icon = svnstatus_to_icon(file.svnstatus);
        if (icon)
            td.appendChild(dom_make_img(icon, icon_size, icon_size,
                                        svnstatus_to_string(file.svnstatus)));
        row.appendChild(td);

        /* Column 3: Filename */
        td = dom_make_link_elem("td", filename,
                "Navigate to " + path_join(path, filename),
                build_revision_url(path, filename, current_revision),
                null, true);
        $(td).click(select_row);
        row.appendChild(td);

        /* Column 4: Size */
        td = dom_make_text_elem("td", nice_filesize(file.size));
        $(td).click(select_row);
        row.appendChild(td);

        /* Column 5: Date */
        td = dom_make_text_elem("td", file.mtime_short, file.mtime_nice);
        $(td).click(select_row);
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

