/* IVLE
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
 */

/* Module: SpecialHome (File Browser, client)
 * Author: David Coles
 * Date: 23/7/2008
 */

/* This module implements the functionality to lay out a special home directory 
 * view on top of the normal listing
 */

/* The name of the personal file directory */
PERSONALDIR="mywork"

/* LAYOUT FUNCTIONS */

/** Present home directory 
 */
function home_listing(listing, subjects, path)
{
    /* Nav through the top-level of the JSON to the actual listing object. */
    var listing = listing.listing;
    
    var filetablediv = document.getElementById("filetablediv");
    var specialhomediv;
    var h2;
    var h3;
    var ul;
    var li;
    var div;

    /* Only show special headings if we get subject listings */
    if (subjects != null)
    {
        /* Wrap all this "special" stuff in a div, for styling purposes */
        specialhomediv = document.createElement("div");
        specialhomediv.setAttribute("id", "specialhome");
        filetablediv.appendChild(specialhomediv);

        /* SUBJECTS Section
        /* Create the header row */
        if (subjects.length > 0)
        {
            h2 = dom_make_text_elem("h2", "Subjects");
            specialhomediv.appendChild(h2);
        }

        /* Create the contents */
        for (var i=0; i<subjects.length; i++)
        {
            var subject = subjects[i];
            var subjpath = subject.subj_short_name;
            // Header
            h3 = dom_make_text_elem("h3", subject.subj_name);
            specialhomediv.appendChild(h3);
        
            /* Print the file listing */
            ul = document.createElement("ul");
            // Stuff
            ul.appendChild(make_subject_item(subjpath,
                path_join("users", username, subjpath), PERSONALDIR,
                "Your own files in this subject"));

            // Groups
            var groups = subject.groups;
            for (var j=0; j<subject.groups.length; j++)
            {
                var group = subject.groups[j];
                ul.appendChild(make_subject_item(subjpath,
                    path_join("groups", subject.subj_short_name + "_" +
                              subject.year + "_" + subject.semester + "_" +
                              group.name),
                    group.name,
                    "This group's files in this subject"));
            }
            
            specialhomediv.appendChild(ul);

            /* Remove it from listing */
            if (subject.subj_short_name in listing)
                delete listing[subject.subj_short_name];
        }

        /* FIXME: Old Subjects? */

        /* STUFF Section -- For the stuff directory */
        /* Create the header */
        h2 = dom_make_text_elem("h2", "Stuff");
        specialhomediv.appendChild(h2);
        /* Create the contents */
        ul = document.createElement("ul");
        ul.appendChild(make_subject_item("",
              path_join("users", username, "stuff"), "stuff",
              "Your own files not related to a subject"));
        specialhomediv.appendChild(ul);
        /* Remove stuff from the listing */
        if ("stuff" in listing)
            delete listing["stuff"];

        /* JUNK Section -- All the rest */
        /* Create the header row */
        if (obj_length(listing) > 0)
        {
            h2 = dom_make_text_elem("h2", "Junk");
            specialhomediv.appendChild(h2);
            handle_dir_listing(path, listing);
        }
    }
    else
    {
        handle_dir_listing(path, listing);
    }
}

/* Does an series of AJAX requests to find out the properties of this folder 
 * and then updates the folder view
 */
function make_subject_item(path, repopath, name, description)
{
    // Create the temporary item
    var li = document.createElement("li");
    var span;
    li.setAttribute("class", "listing-loading");
    li.appendChild(dom_make_text_elem("span", name, description));
    span = dom_make_text_elem("loading...");
    span.setAttribute("class","status");
    li.appendChild(span);

    // Set the callback function to update when we get the real details
    var callback = function(response)
    {
        var sublisting = decode_response(response);
        dom_removechildren(li);
        li.setAttribute("class", "listing-dir");

        // If we could find the file status...
        if (sublisting != null)
        {
            var thisdir = sublisting.listing['.'];
            var versioned = ("svnstatus" in thisdir) && (thisdir.svnstatus != "unversioned");
            if (versioned)
            {
                // Default: Just offer a link to the directory
                li.appendChild(dom_make_link_elem("span", name, description,
                    app_path(this_app, username, path, name)));
            }
            else
            {
                // Blocked: Offer to rename the directory
                li.appendChild(dom_make_text_elem("span", name, description));
                span = dom_make_text_elem("span", " (blocked) ",
                      "Another file or directory is in the way of this directory.");
                span.setAttribute("class", "status");
                li.appendChild(span);

                var button = document.createElement("input");
                $(button).click(function(event)
                {
                    action_rename(path_join(path, name));
                });
                button.setAttribute("type", "button");
                button.setAttribute("value", "Rename");
                span.appendChild(button);
            }
        }
        else
        {
            // Missing: Try to check out or create the repository
            li.appendChild(dom_make_text_elem("span", name, description));
            span = dom_make_text_elem("span", " (missing) ",
                  "This directory does not yet exist.");
            span.setAttribute("class", "status");
            li.appendChild(span);

            var button = document.createElement("input");
            $(button).click(function(event)
            {
                li.setAttribute("class", "listing-loading");

                var localpath = path_join(path, name);

                if (create_if_needed(repopath))
                {
                    // Try a checkout
                    do_act("svncheckout", {"path": [repopath, localpath]});
                }
                else
                {
                    li.setAttribute("class", "listing-dir");
                }
            });
            button.setAttribute("type", "button");
            button.setAttribute("value", "Checkout");
            span.appendChild(button);
        }
    }

    /* Are we working in a subdirectory or parent? */
    ajax_call(callback, service_app, path_join(username, path, name), {}, "GET");
    return li;
}

function create_if_needed(path)
{
    response = ajax_call(null, service_app, current_path,
            {
                "action": "svnrepostat",
                "path": path
            }, "POST");


    if (response.status == 200)
    {
        return true;
    }
    else if (response.status == 404)
    {
        // Try a mkdir
        r2 = ajax_call(null, service_app, current_path,
                {
                    "action": "svnrepomkdir",
                    "path": path,
                    "logmsg": "Automated creation of '" + path + "' work directory"
                }, "POST");

        if (r2.status == 200)
        {
            return true;
        }
    }
    alert("Error: Could not create Subversion directory");
    return false;
}

/** Finds the length (number of user defined properties) of an object
 */
function obj_length(obj)
{
    len = 0;
    for (prop in obj)
        len++;
    return len;
}
