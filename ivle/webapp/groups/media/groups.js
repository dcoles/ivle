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
        alert("Error: Could not add group. Does it already exist?");
    }
    /* Reload the display */
    window.location.href = window.location.href;
}

function manage_group(offeringid, groupid, namespace)
{
    var elem = document.getElementById(namespace);
    var button = document.getElementById(namespace+"_button");
    var manage_div = document.createElement("div")
    manage_div.id = namespace + "_contents";
    elem.insertBefore(manage_div, button);
    
    /* Refresh contents */
    list_projectgroup_contents(offeringid, groupid, manage_div.id);

    /* Remove the button element */
    elem.removeChild(button);
}

/* Lists the information about a particular project group identified by groupid 
 * in an offering identified by offeringid in the element with id elemnm. May 
 * be called multiple times safely to refresh the displayed information.
 */
function list_projectgroup_contents(offeringid, groupid, elemnm)
{
    var contents = document.getElementById(elemnm);
    dom_removechildren(contents);
    var callback = function(xhr)
    {
        var members = JSON.parse(xhr.responseText);
        var available = members.available;
        var groupmembers = members.groupmembers;
        
        /* Existing members */
        var ul = document.createElement("ul");
        for (var i=0; i<groupmembers.length; i++)
        {
            var li = dom_make_text_elem("li", groupmembers[i].fullname + " (" +
                                              groupmembers[i].login + ")");
            ul.appendChild(li);
        }

        /* Add member box */
        var add_li = document.createElement("li");
        var select = document.createElement("select");
        for (var i=0; i<available.length; i++)
        {
            var option = dom_make_text_elem("option", available[i].login);
            option.value = available[i].login;
            select.appendChild(option);
        }
        var button = document.createElement("input");
        button.value = "Add";
        button.type = 'button';
        button.addEventListener("click", function()
        {
            this.disabled = true;
            args = {'login': select.value, 'groupid': groupid};
            ajax_call(null, serviceapp, 'assign_group', args, 'POST');
            list_projectgroup_contents(offeringid, groupid, elemnm);
        }, false);
        add_li.appendChild(select);
        add_li.appendChild(button);
        ul.appendChild(add_li);
        contents.appendChild(ul);
    }
    var args = {'offeringid': offeringid, 'groupid': groupid};
    ajax_call(callback, serviceapp, 'get_group_membership', args, 'GET');

}
