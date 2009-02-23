/* IVLE - Informatics Virtual Learning Environment
 * Copyright (C) 2007-2009 The University of Melbourne
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
 * Author: Nick Chadwick
 */

/* Called when a form upload comes back (from an iframe).
 * Refreshes the page.
 */

function editworksheet()
{
    /* Get the worksheet code the admin is submitting */
    var namearea = document.getElementById("worksheet_name");
    var check_box = document.getElementById("worksheet_asses");
    var sheet_area = document.getElementById("worksheet_data");
    var format_opt = document.getElementById("worksheet_format");
    
    var worksheetname = namearea.value;
    var assessable = check_box.checked;
    var data = sheet_area.value;
    var format = format_opt.value;

    var args = {'ivle.op': 'save', 'data': data, 'assessable': assessable,
                'name': worksheetname, 'format': format};

    /* Send the form as multipart/form-data, since we are sending a whole lump
     * of Python code, it should be treated like a file upload. */
    /* AJAX callback function */
    var callback = function(xhr)
        {
            var testresponse;
            try
            {
                testresponse = JSON.parse(xhr.responseText);
                alert("Worksheet successfully updated.");
            }
            catch (ex)
            {
                alert("There was an error submitting your worksheet. "
                    + "Please notify the administrators of this.");
                return;
            }
        }
    //XXX: This shouldn't be generated here
    save_path = "api/subjects/" + subject + "/" + year + "/" + semester + 
        "/+worksheets/" + worksheet;
    ajax_call(callback, save_path, "", args, "POST");
}

function addworksheet()
{
    /* Get the worksheet code the admin is submitting */
    var idarea = document.getElementById("worksheet_identifier");
    var namearea = document.getElementById("worksheet_name");
    var check_box = document.getElementById("worksheet_asses");
    var sheet_area = document.getElementById("worksheet_data");
    var format_opt = document.getElementById("worksheet_format");
    
    var worksheet_identifier = idarea.value;
    var worksheetname = namearea.value;
    var assessable = check_box.checked;
    var data = sheet_area.value;
    var format = format_opt.value;

    var args = {'ivle.op': 'add_worksheet', 'data': data, 'assessable': 
        assessable, 'name': worksheetname, 'identifier': worksheet_identifier,
        'format': format};

    /* Send the form as multipart/form-data, since we are sending a whole lump
     * of Python code, it should be treated like a file upload. */
    /* AJAX callback function */
    var callback = function(xhr)
        {
            var testresponse;
            try
            {
                testresponse = JSON.parse(xhr.responseText);
                alert("Worksheet successfully saved.");
                window.location = "./";
            }
            catch (ex)
            {
                alert("There was an error submitting your worksheet. "
                    + "Please notify the administrators of this.");
                return;
            }
        }
    //XXX: This shouldn't be generated here
    save_path = "api/subjects/" + subject + "/" + year + "/" + semester +
                "/+worksheets";
    ajax_call(callback, save_path, "", args, "POST");
}
