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

function tog(something)
{
  $('#' + something).toggle("slow");
}

function save_exercise()
{

    var exercise_id = $('#exercise_id').val();
    var exercise_name = $('#exercise_name').val();
    var exercise_num_rows = $('#exercise_num_rows').val();
    var exercise_desc = $('#exercise_include').val();
    var exercise_partial = $('#exercise_partial').val();
    var exercise_solution = $('#exercise_solution').val();
    var exercise_include = $('#exercise_include').val();
    
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert(testresponse['result']);
            window.location.reload();
            return;
        }
        catch(ex)
        {
            alert('Error updating Exercise');
            return;
        }
    }
    
    update_path = "api/+exercises/" + exercise + "/+edit";
    
    var args = {'name': exercise_name, 'description': exercise_desc, 
                'partial': exercise_partial, 'solution': exercise_solution,
                'include': exercise_include, 'num_rows': exercise_num_rows,
                'ivle.op': 'update_exercise'};
    ajax_call(callback, update_path, "", args, 'POST');
}
