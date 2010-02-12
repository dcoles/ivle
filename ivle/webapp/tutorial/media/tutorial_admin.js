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
 
//XXX: Make this actually move the element, not just reload the page
function move_up(worksheet)
{
    var ws_row = document.getElementById("worksheet_row_" + worksheet);
    var ws_row_index = ws_row.rowIndex;
    
    if (ws_row_index == 1) {
        alert('Item already at top of list.');
        return;
    }
    
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            window.location.reload();
        }
        catch(ex)
        {
            alert('There was an error updating the worksheets list.');
            return;
        }
    }
    
    update_path = "api/subjects/" + subject + "/" + year + "/" + 
                   semester + "/+worksheets";
    var args = {'ivle.op': 'move_up', 'worksheetid': worksheet}
    
    ajax_call(callback, update_path, "", args, 'POST');
}

//XXX: Make this actually move the element, not just reload the page
function move_down(worksheet)
{
    var ws_table = document.getElementById('worksheets_table');
    var ws_row = document.getElementById("worksheet_row_" + worksheet);
    var ws_row_index = ws_row.rowIndex;
    
    if (ws_row_index == (ws_table.rows.length - 1)) {
        alert('Item already at bottom of list.');
        return;
    }
    
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            window.location.reload();
        }
        catch(ex)
        {
            alert('There was an error updating the worksheets list.');
            return;
        }
    }
    
    update_path = "api/subjects/" + subject + "/" + year + "/" + 
                   semester + "/+worksheets";
    var args = {'ivle.op': 'move_down', 'worksheetid': worksheet}
    
    ajax_call(callback, update_path, "", args, 'POST');
}

