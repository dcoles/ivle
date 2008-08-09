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
        for (var i=0; i<projectsets.length; i++)
        {
            var projectset = projectsets[i];
            var groups = projectset.groups;
            var dl = document.createElement("dl");
            dl.appendChild(dom_make_text_elem("dt", "Project Set "+(i+1)));
            var dd = document.createElement("dd");
            var ul = document.createElement("ul");
            dd.appendChild(ul);
            /* Add each group in the project set */
            for (var j=0; j<groups.length; j++)
            {
                var group = groups[j];
                ul.appendChild(dom_make_text_elem("li", group['groupnm']))
            }
            dl.appendChild(dd);
            elem.appendChild(dl);
        }
    }
    ajax_call(callback, serviceapp, 'get_project_groups', {'offeringid': offeringid}, 'GET')
}
