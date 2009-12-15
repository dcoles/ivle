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
  $('#' + something).slideToggle("slow");
}

function add_exercise()
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
            alert('Exercise Created');
            window.location = '/+exercises';
        }
        catch (ex)
        {
            alert('Error: Could not add exercise');
            return;
        }
    }
    
    update_path = "api/+exercises";
    
    var args = {'identifier': exercise_id , 'name': exercise_name, 
                'description': exercise_desc, 'partial': exercise_partial,
                'solution': exercise_solution, 'include': exercise_include,
                'num_rows': exercise_num_rows, 'ivle.op': 'add_exercise'};
    ajax_call(callback, update_path, "", args, 'POST');
    
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

/* Modify, add and delete suites */
function edit_suite(suiteid)
{
    var desc = $('#test_suite_' + suiteid + '_description').val();
    var func = $('#test_suite_' + suiteid + '_function').val();
    var stdin = $('#test_suite_' + suiteid + '_stdin').val();
    
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
    var desc = $('#test_suite_new_description').val();
    var func = $('#test_suite_new_function').val();
    var stdin = $('#test_suite_new_stdin').val();
    
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

function delete_suite(suiteid)
{
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert('Suite Deleted.');
            window.location.reload()
            return;
        }
        catch (ex)
        {
            alert('Could not delete suite.');
        }
        
    }
    
    var args = {'ivle.op': 'delete_suite', 'suiteid': suiteid}
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');
}

/* Modify and add Variables */
function edit_var(varid, suiteid)
{
    var var_name = $('#var_name_' + varid).val();
    var var_val = $('#var_val_' + varid).val();
    var var_type = $('#var_type_' + varid).val();
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

    var args = {'ivle.op': 'edit_var', 'var_name': var_name,
                'var_val': var_val, 'var_type': var_type, 'argno': argno,
                'varid': varid, 'suiteid': suiteid};
    
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST')

}

function add_var(suiteid)
{
    var var_name = $('#new_var_name_' + suiteid).val();
    var var_val = $('#new_var_val_' + suiteid).val();
    var var_type = $('#new_var_type_' + suiteid).val();
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
            alert('Error Adding Variable.');
            return;
        }
    }
    
    var args = {'ivle.op': 'add_var', 'var_name': var_name, 
                'var_val': var_val, 'var_type': var_type, 
                'argno': argno, 'suiteid': suiteid};
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');
}

function delete_var(varid, suiteid)
{
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert('Variable Deleted.');
            window.location.reload();
            return;
        }
        catch(ex)
        {
            alert('Error Deleting Variable');
            return;
        }
    }
    var args = {'ivle.op': 'delete_var', 'suiteid': suiteid, 'varid': varid};
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');

}

/* Add and edit test case parts */

function add_test_case(suiteid)
{
    var passmsg = $("#new_test_case_" + suiteid + "_pass").val();
    var failmsg = $("#new_test_case_" + suiteid + "_fail").val();
    
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert('Test Case Added Sucessfully');
            window.location.reload();
            return;
        }
        catch(ex)
        {
            alert('Error Creating Test Suite');
            return;
        }
    }
    
    var args = {'ivle.op': 'add_testcase', 'passmsg': passmsg, 
                'failmsg': failmsg, 'suiteid': suiteid};
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');
    
}

function edit_test_case(testid, suiteid)
{
    var passmsg = $("#test_case_" + testid + "_" + suiteid + "_pass").val();
    var failmsg = $("#test_case_" + testid + "_" + suiteid + "_fail").val();
    
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert('Test Case Modified Sucessfully');
            return;
        }
        catch(ex)
        {
            alert('Error Saving Test Case');
            return;
        }
    }
    
    var args = {'ivle.op': 'edit_testcase', 'passmsg': passmsg, 
                'failmsg': failmsg, 'testid':testid, 'suiteid': suiteid};
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');
}

function delete_testcase(testid, suiteid)
{
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert('Test Case Deleted.');
            window.location.reload();
            return;
        }
        catch(ex)
        {
            alert('Error Deleting Test Case');
            return;
        }
    }
    
    var args = {'ivle.op': 'delete_testcase', 'testid': testid, 
                'suiteid': suiteid};
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');
}

/* Functions to add, edit, and delete test case parts */
function edit_test_part(partid, testid, suiteid)
{
    var part_type = $("#test_part_" + partid + "_part_type").val();
    var test_type = $("input[name='test_part_" + partid + "_test_type']:checked").val();
    var data = $("#test_part_" + partid + "_data").val();
    
    var callback = function(xhr)
    {
        var testresponse;
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert("Test Part Modified");
        }
        catch (ex)
        {
            alert("Error Adding Test Part");
            return;
        }
    }
    
    var args = {'ivle.op': 'edit_testpart', 'part_type': part_type, 
                'test_type': test_type, 'data': data, 'partid': partid,
                'testid': testid, 'suiteid': suiteid};
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');
}

function add_test_part(testid, suiteid)
{
    var part_type = $("#test_part_new_part_type_" + testid).val();
    var test_type = $("input[name='test_part_new_" + testid + "_test_type']:checked").val();
    var data = $("#test_part_new_" + testid + "_data").val();

    var savebutton = $("#new_test_part_save_" + testid);
    savebutton.attr('value', 'Saving...');
    savebutton.attr('disabled', 'disabled');
    
    var callback = function(xhr)
    {
        var testresponse;
        var test_part_id;
        var test_parts = $("#test_case_parts_" + testid);
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            savebutton.attr('value', 'Saving...');
            savebutton.removeAttr('disabled');
            
            alert("Test Part Added");
            window.location.reload();
            return;
        }
        catch (ex)
        {
            alert("Error Adding Test Part");
            return;
        }
    }
    
    var args = {'ivle.op': 'add_testpart', 'part_type': part_type, 
                'test_type': test_type, 'data': data, 'testid': testid,
                'suiteid': suiteid};
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');
}

function delete_testpart(partid, testid, suiteid)
{
    var callback = function(xhr)
    {
        try
        {
            testresponse = JSON.parse(xhr.responseText);
            alert("Test Part Deleted.");
            window.location.reload();
            return;
        }
        catch (ex)
        {
            alert("Error Deleting Test Part");
            return;
        }
    }
    
    var args = {'ivle.op': 'delete_testpart', 'partid': partid, 
                'testid': testid, 'suiteid': suiteid};
    update_path = "api/+exercises/" + exercise;
    ajax_call(callback, update_path, "", args, 'POST');
}

function enable_test_part_function(partid, which)
{
    var elem = $("#test_part_" + partid + "_data");
    if (which)
        elem.removeAttr("disabled");
    else
        elem.attr("disabled", "disabled");
}

/* Set a test part's code to a reasonable default. This clobbers any
 * code that is present.
 */
function set_test_part_function(partid, test_type)
{
    var defaults = new Object();
    defaults.match = "";
    defaults.norm = "lambda x: x";
    defaults.check = "lambda solution, attempt: solution == attempt";

    $("#test_part_" + partid + "_data").text(defaults[test_type]);
}

/* When a test part's test type (norm/check/match) is changed, enable
 * or disable the code textarea and set some example code.
 */
function test_part_type_changed(partid)
{
    var name = "test_part_" + partid + "_test_type";
    var enable = true;
    var test_type = $("input[name='" + name + "']:checked").val();
    var sample_code = "";

    if (test_type == "match")
        enable = false;

    enable_test_part_function(partid, enable);
    set_test_part_function(partid, test_type);
};

/* When a test suite's function checkbox is toggled, enable or
 * disable and clear the textbox.
 */
function test_suite_function_enabled(suiteid)
{
    var name = "test_suite_" + suiteid + "_function";
    var textbox_elem = $("#" + name);

    if ($("#" + name + "_enabled").is(":checked"))
        textbox_elem.removeAttr("disabled")
    else
    {
        textbox_elem.attr("disabled", "disabled");
        textbox_elem.val("");
    }
};
