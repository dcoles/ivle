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

/* Show and hide the given page element */
function tog(something)
{
  $('#' + something).toggle("slow");
}

/* Edit the exercise values */
function edit_exercise()
{

    var exercise_id = $('#exercise_id').val();
    var exercise_name = $('#exercise_name').val();
    var exercise_num_rows = $('#exercise_num_rows').val();
    var exercise_desc = $('#exercise_desc').val();
    var exercise_partial = $('#exercise_partial').val();
    var exercise_solution = $('#exercise_solution').val();
    var exercise_include = $('#exercise_include').val();
    
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert('Exercise Saved');
            return;
        }
        catch(ex)
        {
            alert('Error updating Exercise');
            return;
        }
    }
    
    update_path = "api/+exercises/" + exercise;
    
    var args = {'name': exercise_name, 'description': exercise_desc, 
                'partial': exercise_partial, 'solution': exercise_solution,
                'include': exercise_include, 'num_rows': exercise_num_rows,
                'ivle.op': 'edit_exercise'};
    ajax_call(callback, update_path, "", args, 'POST');
}

/* Modify and add suites */
function edit_suite(suiteid)
{
    var desc = $('#test_suite_description_' + suiteid).val();
    var func = $('#test_suite_function_' + suiteid).val();
    var stdin = $('#test_suite_stdin_' + suiteid).val();
    
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert('Suite Saved');
            window.location.reload();
            return;
        }
        catch(ex)
        {
            alert('Error Saving Test Suite');
            return;
        }
    }
    
    var args = {'ivle.op': 'edit_suite', 'description': desc, 'function': func,
                'stdin': stdin, 'suiteid': suiteid};
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');
}

function add_suite()
{
    var desc = $('#new_test_suite_description').val();
    var func = $('#new_test_suite_function').val();
    var stdin = $('#new_test_suite_stdin').val();
    
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert('Suite Created Sucessfully');
            window.location.reload();
            return;
        }
        catch(ex)
        {
            alert('Error Creating Test Suite');
        }
    }
    
    var args = {'ivle.op': 'add_suite', 'description': desc, 'function': func,
                'stdin': stdin};
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');
}

/* Modify and add Variables */
function edit_var(varid)
{
    var var_name = $('#var_type_' + varid).val();
    var var_val = $('#var_val' + varid).val();
    var var_type = $('#var_name_' + varid).val();
    var argno = $('#var_argno_' + varid).val();

    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert('Variable Added Sucessfully');
            window.location.reload();
            return;
        }
        catch(ex)
        {
            alert('Error Creating Test Suite');
            return;
        }
    }

    var args = {'ivle.op': 'edit_var'};
    
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST')

}

function add_var(suiteid)
{
    var var_name = $('#new_var_type_' + suiteid).val();
    var var_val = $('#new_var_val' + suiteid).val();
    var var_type = $('#new_var_name_' + suiteid).val();
    var argno = $('#new_var_argno_' + suiteid).val();
    
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert('Variable Added Sucessfully');
            window.location.reload();
            return;
        }
        catch(ex)
        {
            alert('Error Creating Test Suite');
            return;
        }
    }
    
    var args = {'ivle.op': 'add_var', 'var_name': var_name, 
                'var_val': var_val, 'var_type': var_type, 
                'argno': argno, 'suiteid': suiteid};
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');
}

/* Add and edit test case parts */

function add_test_case(suiteid)
{
    var passmsg = $("new_test_case_pass_" + suiteid).val();
    var failmsg = $("new_test_case_fail_" + suiteid).val();
    var case_default = $("new_test_case_default_" + suiteid).val();
    
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert('Variable Added Sucessfully');
            window.location.reload();
            return;
        }
        catch(ex)
        {
            alert('Error Creating Test Suite');
            return;
        }
    }
    
}
