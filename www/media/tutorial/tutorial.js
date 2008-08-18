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
 * Module: Tutorial system (client)
 * Author: Matt Giuca
 * Date: 25/1/2008
 */

/** User clicks "Run" button. Do an Ajax call and print the test output.
 */
function runexercise(exerciseid, filename)
{
    /* Get the source code the student is submitting */
    var exercisediv = document.getElementById(exerciseid);
    var exercisebox = exercisediv.getElementsByTagName("textarea")[0];
    var code = exercisebox.value;

    /* Dump the entire file to the console */
    var callback = function()
    {
        console_enter_line(code, "block");
    }
    start_server(callback)
    return;
}

/** Given a response object (JSON-parsed object), displays the result of the
 * test to the user. This modifies the given exercisediv's children.
 */
function handle_runresponse(exercisediv, runresponse)
{
    var runoutput = exercisediv.getElementsByTagName("textarea")[1];
    dom_removechildren(runoutput);
    runoutput.appendChild(document.createTextNode(runresponse.stdout));
}

/** User clicks "Submit" button. Do an Ajax call and run the test.
 * exerciseid: "id" of the exercise's div element.
 * filename: Filename of the exercise's XML file (used to identify the exercise
 *     when interacting with the server).
 */
function submitexercise(exerciseid, filename)
{
    var original_saved_status = get_saved_status(exerciseid);
    set_submit_status(exerciseid, filename, "Submitting...");
    set_saved_status(exerciseid, filename, "Saving...");
    /* Get the source code the student is submitting */
    var exercisediv = document.getElementById(exerciseid);
    var exercisebox = exercisediv.getElementsByTagName("textarea")[0];
    var code = exercisebox.value;

    var args = {"code": code, "exercise": filename, "action": "test"};

    /* Send the form as multipart/form-data, since we are sending a whole lump
     * of Python code, it should be treated like a file upload. */
    /* AJAX callback function */
    var callback = function(xhr)
        {
            var testresponse;
            try
            {
                testresponse = JSON.parse(xhr.responseText);
            }
            catch (ex)
            {
                alert("There was an error submitting or running your code. "
                    + "Please notify the administrators of this.");
                /* Since it failed, set the Save button back how it was. */
                set_saved_status(exerciseid, filename, original_saved_status);
                set_submit_status(exerciseid, filename, "Submit");
                return;
            }
            handle_testresponse(exercisediv, exerciseid, testresponse);
            set_saved_status(exerciseid, filename, "Saved");
            set_submit_status(exerciseid, filename, "Submit");
            /* Close the "view previous" area (force reload) */
            close_previous(exerciseid);
        }
    ajax_call(callback, "tutorialservice", "", args, "POST",
        "multipart/form-data");
}

/** User clicks "Save" button. Do an Ajax call to store it.
 * exerciseid: "id" of the exercise's div element.
 * filename: Filename of the exercise's XML file (used to identify the exercise
 *     when interacting with the server).
 */
function saveexercise(exerciseid, filename)
{
    set_saved_status(exerciseid, filename, "Saving...");
    /* Get the source code the student is submitting */
    var exercisediv = document.getElementById(exerciseid);
    var exercisebox = exercisediv.getElementsByTagName("textarea")[0];
    var code = exercisebox.value;

    var args = {"code": code, "exercise": filename, "action": "save"};

    /* Send the form as multipart/form-data, since we are sending a whole lump
     * of Python code, it should be treated like a file upload. */
    /* AJAX callback function */
    var callback = function(xhr)
        {
            // XXX Maybe check to see if this worked?
            set_saved_status(exerciseid, filename, "Saved");
        }
    ajax_call(callback, "tutorialservice", "", args, "POST",
        "multipart/form-data");
}

/** User clicks "Reset" button. Replace the contents of the user program text
 * box with the hidden "reset button backup" field, containing the original
 * partial fragment.
 * exerciseid: "id" of the exercise's div element.
 * filename: Filename of the exercise's XML file (used to identify the exercise
 *     when interacting with the server).
 */
function resetexercise(exerciseid, filename)
{
    conf_msg = "This will delete your solution to this exercise, and reset "
        + "it back to the default partial solution.\n\n"
        + "Are you sure you want to do this?";
    if (!confirm(conf_msg))
        return;
    /* Get the source code the student is submitting */
    var exercisediv = document.getElementById(exerciseid);
    var exercisebox = exercisediv.getElementsByTagName("textarea")[0];
    var resettextbox = document.getElementById("input_resettext_" + exerciseid);
    var text_urlencoded = resettextbox.value;
    /* Need to un-urlencode the value */
    exercisebox.value = decodeURIComponent(text_urlencoded);
    /* We changed the text, so make Save button available, and autosave after
     * 10 seconds. */
    set_saved_status(exerciseid, filename, "Save");
}

/* savetimers is a dict mapping exerciseIDs to timer IDs.
 * Its members indicate all exercises that have been modified but not saved.
 */
savetimers = {}

/** Changes whether an exercise is considered "saved" or not.
 * stat is a string which specifies the status, and also the button text.
 * If stat == "Save", then it indicates it is NOT saved. This will
 * enable the "Save" button, and set a timer going which will auto-save
 * after a set period of time (eg. 30 seconds).
 * Any other value will disable the "Save" button and disable the timer.
 * stat should be "Saving..." when the save request is issued, and "Saved"
 * when the response comes back.
 */
function set_saved_status(exerciseid, filename, stat)
{
    var timername = "savetimer_" + exerciseid;
    var button = document.getElementById("savebutton_" + exerciseid);
    var is_saved = stat != "Save";
    button.value = stat;

    /* Disable the timer, if it exists */
    if (typeof(savetimers[timername]) != "undefined")
    {
        clearTimeout(savetimers[timername]);
        savetimers[timername] = undefined;
    }

    if (is_saved)
    {
        /* Disable the button */
        button.disabled = true;
    }
    else
    {
        /* Enable the button */
        button.disabled = false;
        /* Create a timer which will auto-save when it expires */
        var save_string = "saveexercise(" + repr(exerciseid) + ", "
            + repr(filename) + ")"
        savetimers[timername] = setTimeout(save_string, 10000);
    }
}

/** Retrieves the saved status of a given exercise.
 * Returns "Save" if the exercise is modified and needs to be saved.
 * Returns "Saved" if the exercise has been saved and is unmodified.
 * Returns "Saving..." if the exercise is in the process of being saved
 *  (an ajax request is on its way).
 */
function get_saved_status(exerciseid)
{
    var button = document.getElementById("savebutton_" + exerciseid);
    return button.value;
}

/** Changes the state of the submit button, so it can appear disabled during
 * the submission process (to avoid multiple clicks).
 * stat is a string which specifies the status, and also the button text.
 * If stat == "Submit", then it indicates it is available for submission.
 * This will enable the "Submit" button.
 * Any other value (recommended: "Submitting...") will disable the "Submit"
 * button.
 */
function set_submit_status(exerciseid, filename, stat)
{
    var button = document.getElementById("submitbutton_" + exerciseid);
    button.disabled = stat != "Submit";
    button.value = stat;
}

/** Given a exercise div, return the testoutput div which is its child.
 * (The div which is its child whose class is "testoutput".
 */
function get_testoutput(exercisediv)
{
    var childs = exercisediv.childNodes;
    var i;
    var testoutput;
    for (i=0; i<childs.length; i++)
        if (childs[i].nodeType == exercisediv.ELEMENT_NODE &&
            childs[i].getAttribute("class") == "testoutput")
            return childs[i];
    return null;
}

/** Given a response object (JSON-parsed object), displays the result of the
 * test to the user. This modifies the given exercisediv's children.
 */
function handle_testresponse(exercisediv, exerciseid, testresponse)
{
    var testoutput = get_testoutput(exercisediv);
    var i, j;
    var ul;
    var case_ul;
    if (testoutput == null) return;     /* should not happen */
    dom_removechildren(testoutput);

    ul = document.createElement("ul");
    testoutput.appendChild(ul);

    if ("critical_error" in testresponse)
    {
        /* Only one error - and it's bad.
         * Just print and stop */
        ul.appendChild(create_response_item("critical", 0,
            testresponse.critical_error.name,
            testresponse.critical_error.detail));
        return;
    }

    for (i=0; i<testresponse.cases.length; i++)
    {
        var testcase = testresponse.cases[i];
        if ("exception" in testcase)
        {
            /* User's code threw an exception */
            fail_li = create_response_item("fail", 0, testcase.name);
            ul.appendChild(fail_li);
            /* Create a sub-ul to display the failing cases. */
            case_ul = document.createElement("ul");
            fail_li.appendChild(case_ul);
            case_ul.appendChild(create_response_item("exception", 0,
                testcase.exception.name, testcase.exception.detail));
        }
        else if (testcase.passed)
        {
            /* All parts of the test case passed. Just report the overall case
             * passing. */
	    ul.appendChild(create_response_item("pass", 0, testcase.name));
        }
        else
        {
            var fail_li = create_response_item("fail", 0, testcase.name);
            ul.appendChild(fail_li);
            /* Create a sub-ul to display the failing cases. */
            case_ul = document.createElement("ul");
            fail_li.appendChild(case_ul);
            
            for (j=0; j<testcase.parts.length; j++)
            {
                var part = testcase.parts[j];
                if (part.passed)
                {
                    case_ul.appendChild(create_response_item("pass", 1,
                        part.description));
                }
                else
                {
                    case_ul.appendChild(create_response_item("fail", 1,
                        part.description /*, part.error_message */));
                }
            }
        }
    }

    /* Update the summary box (completed, attempts) with the new values we got
     * back from the tutorialservice.
     * (Also update the balls in the table-of-contents).
     */
    var toc_li = document.getElementById("toc_li_" + exerciseid);
    var summaryli = document.getElementById("summaryli_" + exerciseid);
    var summarycomplete = document.getElementById("summarycomplete_"
        + exerciseid);
    var summaryattempts = document.getElementById("summaryattempts_"
        + exerciseid);
    toc_li.setAttribute("class",
        (testresponse.completed ? "complete" : "incomplete"));
    summaryli.setAttribute("class",
        (testresponse.completed ? "complete" : "incomplete"));
    summarycomplete.removeChild(summarycomplete.lastChild);
    summarycomplete.appendChild(document.createTextNode(testresponse.completed
        ? "Complete" : "Incomplete"));
    var old_attempts_value = summaryattempts.lastChild.data;
    summaryattempts.removeChild(summaryattempts.lastChild);
    summaryattempts.appendChild(document.createTextNode(
        testresponse.attempts));
    if (testresponse.completed && testresponse.attempts == 1 &&
        old_attempts_value == "0")
    {
        /* Add "Well done" for extra congratulations */
        summaryli.appendChild(document.createTextNode(
            " Well done!"));
    }
}

/* DOM creators for test case response elements */

/** Create a <li> element for the result of a test case.
 * type: "pass", "fail", "exception" or "critical"
 * level is 0 for outer, and 1 for inner
 * For exceptions and crits, "desc" is the exception name,
 * detail is the message; detail should be null for passing cases.
 */
function create_response_item(type, level, desc, detail)
{
    var crit = false;
    if (type == "critical")
    {
        /* Crits look like exceptions, but are slightly different */
        crit = true;
        type = "exception";
    }
    var li = document.createElement("li");
    if (level == 0)
    {
        li.setAttribute("class", type);
    }
    else
    {
        if (type == "pass") { li.setAttribute("class", "check") }
        else { li.setAttribute("class", "cross") }
    }

    if (level == 0) /* print Pass/Fail tag at outer level only */
    {
        var b = document.createElement("b");
        var text = type.charAt(0).toUpperCase() + type.substr(1) + ":";
        b.appendChild(document.createTextNode(text));
        li.appendChild(b);
    }

    if (type == "pass")
        text = desc;
    else if (type == "fail")
        text = desc + (detail == null ? "" : ":");
    else if (type == "exception")
    {
        if (crit)
            text = "Your code could not be executed, "
                + "due to the following error:";
        else
            text = "The following exception occured "
                + "while running your code:";
    }
    li.appendChild(document.createTextNode(" " + text));
    if (type == "pass" || (type == "fail" && detail == null))
        return li;

    /* Non-passes, display the error message */
    li.appendChild(document.createElement("br"));
    if (type == "exception")
    {
        b = document.createElement("b");
        b.appendChild(document.createTextNode(desc + ":"));
        li.appendChild(b);
    }
    li.appendChild(document.createTextNode(detail));
    return li;
}

/** Special key handlers for exercise text boxes */
function catch_textbox_input(exerciseid, filename, key)
{
    /* NOTE: Copied and modified from console/console.js:catch_input. */
    /* Always update the saved status, so it will enable the save button and
     * auto-save timer. */
    set_saved_status(exerciseid, filename, "Save");
    var inp = document.getElementById('textarea_' + exerciseid);
    switch (key)
    {
    case 9:                 /* Tab key */
        var selstart = inp.selectionStart;
        var selend = inp.selectionEnd;
        var chars_added;
        if (selstart == selend)
        {
            /* No selection, just a carat. Insert a tab here. */
            inp.value = inp.value.substr(0, selstart)
                + TAB_STRING + inp.value.substr(selstart);
            chars_added = TAB_STRING.length;
        }
        else
        {
            /* Text is selected.
             * Indent each line that is selected.
             */
            var pre_sel = inp.value.substr(0, selstart);
            var in_sel = inp.value.substr(selstart, selend-selstart);
            var post_sel = inp.value.substr(selend);
            console.log("pre_sel = " + repr(pre_sel));
            console.log("in_sel = " + repr(in_sel));
            console.log("post_sel = " + repr(post_sel));
            /* Move everything after the last newline in pre_sel to in_sel,
             * so it will be indented too (ie. the first line
             * partially-selected). */
            var pre_sel_newline = pre_sel.lastIndexOf('\n')+1;
            in_sel = pre_sel.substr(pre_sel_newline) + in_sel;
            pre_sel = pre_sel.substr(0, pre_sel_newline);
            /* Now insert TAB_STRING before each line of in_sel */
            in_sel = in_sel.split('\n');
            var new_in_sel = TAB_STRING + in_sel[0]
            for (var i=1; i<in_sel.length; i++)
                new_in_sel += '\n' + TAB_STRING + in_sel[i];
            chars_added = TAB_STRING.length * in_sel.length;

            inp.value = pre_sel + new_in_sel + post_sel;
        }
        /* Update the selection so the same characters as before are selected
         */
        inp.selectionStart = selstart + chars_added;
        inp.selectionEnd = inp.selectionStart + (selend - selstart);
        /* Cancel the event, so the TAB key doesn't move focus away from this
         * box */
        return false;
        /* Note: If it happens that some browsers don't support event
         * cancelling properly, this hack might work instead:
        setTimeout(
            "document.getElementById('console_inputText').focus()",
            0);
         */
        break;
    }
}

/** User clicks "view previous attempts" button. Do an Ajax call and populate.
 * exerciseid: "id" of the exercise's div element.
 * filename: Filename of the exercise's XML file (used to identify the
 *     exercise when interacting with the server).
 */
function open_previous(exerciseid, filename)
{
    var exercisediv = document.getElementById(exerciseid);
    var divs = exercisediv.getElementsByTagName("div");
    var attempthistory;
    for (var i=0; i<divs.length; i++)
        if (divs[i].getAttribute("class") == "attempthistory")
            attempthistory = divs[i];

    /* Get handles on the four existing elements of the history box */
    var openbutton = attempthistory.getElementsByTagName("p")[0];
    var openarea = attempthistory.getElementsByTagName("div")[0];
    var dropdown = attempthistory.getElementsByTagName("select")[0];
    var textarea = attempthistory.getElementsByTagName("textarea")[0];

    /* Activate the "open" state, and clear the dropdown box */
    openbutton.setAttribute("style", "display: none");
    openarea.setAttribute("style", "display: auto");
    textarea.setAttribute("style", "display: none");
    dom_removechildren(dropdown);
    var pleasewait = document.createElement("option");
    pleasewait.appendChild(document.createTextNode("Retrieving past attempts..."));
    dropdown.appendChild(pleasewait);

    var args = {"exercise": filename, "action": "getattempts"};

    /* Send the form as multipart/form-data, since we are sending a whole lump
     * of Python code, it should be treated like a file upload. */
    /* AJAX callback function */
    var callback = function(xhr)
        {
            var attempts;
            var attempt;
            var opt;
            try
            {
                attempts = JSON.parse(xhr.responseText);
            }
            catch (ex)
            {
                alert("There was an error fetching your attempt history. "
                    + "Please notify the administrators of this.");
                return;
            }
            /* Populate the attempt history div */
            dom_removechildren(dropdown);
            for (var i=0; i<attempts.length; i++)
            {
                /* An object with a date and complete */
                attempt = attempts[i];
                opt = document.createElement("option");
                opt.setAttribute("value", attempt.date);
                opt.appendChild(document.createTextNode(attempt.date));
                if (attempt.complete)
                {
                    /* Add a little green ball to this option
                     * This is probably hideously illegal, but looks nice :)
                     */
                    opt.appendChild(document.createTextNode(" "));
                    var img = document.createElement("img");
                    img.setAttribute("src",
                        make_path("media/images/tutorial/tiny/complete.png"));
                    img.setAttribute("alt", "Complete");
                    opt.appendChild(img);
                }
                dropdown.appendChild(opt);
            }
        }
    ajax_call(callback, "tutorialservice", "", args, "GET");
}

function close_previous(exerciseid)
{
    var exercisediv = document.getElementById(exerciseid);
    var divs = exercisediv.getElementsByTagName("div");
    var attempthistory;
    for (var i=0; i<divs.length; i++)
        if (divs[i].getAttribute("class") == "attempthistory")
            attempthistory = divs[i];

    /* Get handles on the four existing elements of the history box */
    var openbutton = attempthistory.getElementsByTagName("p")[0];
    var openarea = attempthistory.getElementsByTagName("div")[0];

    /* Deactivate the "open" state */
    openbutton.setAttribute("style", "display: auto");
    openarea.setAttribute("style", "display: none");
}

/** User selects an attempt in the dropdown. Do an Ajax call and populate.
 * exerciseid: "id" of the exercise's div element.
 * filename: Filename of the exercise's XML file (used to identify the
 *     exercise when interacting with the server).
 */
function select_attempt(exerciseid, filename)
{
    var exercisediv = document.getElementById(exerciseid);
    var divs = exercisediv.getElementsByTagName("div");
    var attempthistory;
    for (var i=0; i<divs.length; i++)
        if (divs[i].getAttribute("class") == "attempthistory")
            attempthistory = divs[i];

    /* Get handles on the four existing elements of the history box */
    var dropdown = attempthistory.getElementsByTagName("select")[0];
    var textarea = attempthistory.getElementsByTagName("textarea")[0];

    /* Get the "value" of the selected option */
    var date = dropdown.options[dropdown.selectedIndex].getAttribute("value");

    var args = {"exercise": filename, "action": "getattempt", "date": date};

    /* Send the form as multipart/form-data, since we are sending a whole lump
     * of Python code, it should be treated like a file upload. */
    /* AJAX callback function */
    var callback = function(xhr)
        {
            var attempt;
            try
            {
                attempt = JSON.parse(xhr.responseText);
            }
            catch (ex)
            {
                alert("There was an error fetching your attempt history. "
                    + "Please notify the administrators of this.");
                return;
            }
            if (attempt == null)
            {
                /* There was no data for this date - that's odd */
                alert("There was no attempt made before that date.");
                return;
            }
            /* Populate the attempt text field */
            textarea.removeAttribute("readonly");
            dom_removechildren(textarea);
            textarea.appendChild(document.createTextNode(attempt));
            textarea.setAttribute("style", "display: auto");
            //textarea.setAttribute("readonly", "readonly");
        }
    ajax_call(callback, "tutorialservice", "", args, "GET");
}
