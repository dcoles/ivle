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

/* Runs at startup. */
function onload()
{
    /* Set up the console plugin to display as a popup window */
    console_init(true);
}

/** User clicks "Run" button. Do an Ajax call and print the test output.
 */
function runexercise(exerciseid, filename)
{
    /* Get the source code the student is submitting */
    var exercisediv = document.getElementById(problemid);
    var exercisebox = exercisediv.getElementsByTagName("textarea")[0];
    var code = exercisebox.value;

    /* Dump the entire file to the console */
    console_enter_line(code, "block");
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
    /* Get the source code the student is submitting */
    var exercisediv = document.getElementById(exerciseid);
    var exercisebox = exercisediv.getElementsByTagName("textarea")[0];
    var code = exercisebox.value;

    var args = {"code": code, "exercise": filename, "action": "test"};

    /* Send the form as multipart/form-data, since we are sending a whole lump
     * of Python code, it should be treated like a file upload. */
    var xhr = ajax_call("tutorialservice", "", args, "POST",
        "multipart/form-data");
    var testresponse = JSON.parse(xhr.responseText);
    handle_testresponse(exercisediv, testresponse);
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
function handle_testresponse(exercisediv, testresponse)
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
        var text = type[0].toUpperCase() + type.substr(1) + ":";
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
