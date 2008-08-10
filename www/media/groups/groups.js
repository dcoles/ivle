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
 * Module: Group management system (client)
 * Author: Matt Giuca
 * Date: 21/7/2008
 */

serviceapp = 'userservice';

function create(offeringid)
{
    /* TODO: Write this function */
}

/* Displays the selected group in the group adminsitration area
 */
function manage_subject()
{
    /* Get the subject id from the select box */
    var subject_select = document.getElementById("subject_select");
    var subject_div = document.getElementById("subject_div");
    var subjectid = parseInt(subject_select.value);

    /* List active offerings */
    dom_removechildren(subject_div);
    var p = dom_make_text_elem("h2", "Active Offerings");
    subject_div.appendChild(p);
    var callback = function(xhr) 
    {
        var offerings = JSON.parse(xhr.responseText);
        for (var i=0; i<offerings.length; i++)
        {
            var offering = offerings[i];
            var text = offering.subj_name + ", Semester " + offering.semester + " " + offering.year;
            var h3 = dom_make_text_elem("h3", text);
            subject_div.appendChild(h3);
            var div = document.createElement("div");
            subject_div.appendChild(div);
            manage_subject_offering(offering['offeringid'], div);
        }
    }
    ajax_call(callback, serviceapp, 'get_active_offerings', {'subjectid': subjectid}, 'GET');
}

/* Manages the display of a single offerings groups
 * Takes a offeringid and element to attach the results to
 */
function manage_subject_offering(offeringid, elem)
{
    var callback = function(xhr)
    {
        var projectsets = JSON.parse(xhr.responseText);
        var dl = document.createElement("dl");
        elem.appendChild(dl);
        /* Add details for each project set */
        for (var i=0; i<projectsets.length; i++)
        {
            var projectset = projectsets[i];
            var groups = projectset.groups;
            
            var dt = dom_make_text_elem("dt", "Project Set "+(i+1)+" ");
            var input = document.createElement("input");
            input.value = "New Group";
            input.type = 'button';
            input.setAttribute("onclick", "create_new_group("+projectset['projectsetid']+")");
            dt.appendChild(input);
            dl.appendChild(dt);
            var dd = document.createElement("dd");
            var ul = document.createElement("ul");
            dd.appendChild(ul);
            /* Add each group in the project set */
            for (var j=0; j<groups.length; j++)
            {
                var group = groups[j];
                var namespace = "project_group_" + group.groupid;
                var li = dom_make_text_elem("li", group['groupnm']+" ");
                li.id = namespace;
                var button = document.createElement("a");
                button.id = namespace+"_button";
                button.setAttribute("class", "choice");
                button.textContent = '(manage)';
                button.setAttribute("onclick",
                    "manage_group("+offeringid+","+group.groupid+",'"+namespace+"')");
                li.appendChild(button);
                ul.appendChild(li);
            }
            dl.appendChild(dd);
        }
    }
    ajax_call(callback, serviceapp, 'get_project_groups', {'offeringid': offeringid}, 'GET');
}

/* Creates a group */
function create_new_group(projectsetid)
{
    groupnm = window.prompt('Please enter a name for the group');
    args = {'projectsetid': projectsetid, 'groupnm':groupnm, 'nick': groupnm};
    response = ajax_call(null, serviceapp, 'create_group', args, 'POST');
    if (response.status == 200)
    {
        /* pass */
    }
    else
    {
        alert("Error: Could not add group. Does it already exits?");
    }
    /* Reload the display */
    manage_subject();
}

function manage_group(offeringid, groupid, namespace)
{
    var elem = document.getElementById(namespace);
    var button = document.getElementById(namespace+"_button");
    var manage_div = document.createElement("div")
    elem.insertBefore(manage_div, button);

    var callback = function(xhr)
    {
        var members = JSON.parse(xhr.responseText);
        var available = members.available;
        var groupmembers = members.groupmembers;
        
        /* Add member box */
        var select = document.createElement("select");
        for (var i=0; i<available.length; i++)
        {
            var option = dom_make_text_elem("option", available[i].login);
            option.value = available[i].login;
            select.appendChild(option);
        }
        var button = document.createElement("input");
        button.value = "Add new group member";
        button.type = 'button';
        button.addEventListener("click", function()
        {
            args = {'login': select.value, 'groupid': groupid};
            ajax_call(null, serviceapp, 'assign_group', args, 'POST');
        }, false);
        manage_div.appendChild(select);
        manage_div.appendChild(button);
        
        /* Existing members */
        manage_div.appendChild(dom_make_text_elem("p", "Group Members:"));
        var ul = document.createElement("ul");
        for (var i=0; i<groupmembers.length; i++)
        {
            var li = dom_make_text_elem("li", groupmembers[i].login);
            ul.appendChild(li);
        }
        manage_div.appendChild(ul);
    }
    var args = {'offeringid': offeringid, 'groupid': groupid};
    ajax_call(callback, serviceapp, 'get_group_membership', args, 'GET');
    /* Remove the button element */
    elem.removeChild(button);
}
