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
function runproblem(problemid, filename)
{
    /* Get the source code the student is submitting */
    var problemdiv = document.getElementById(problemid);
    var problembox = problemdiv.getElementsByTagName("textarea")[0];
    var code = problembox.value;

    var args = {"code": code, "problem": filename, "action": "run"};

    /* Send the form as multipart/form-data, since we are sending a whole lump
     * of Python code, it should be treated like a file upload. */
    var xhr = ajax_call("tutorialservice", "", args, "POST",
        "multipart/form-data");
    var testresponse = JSON.parse(xhr.responseText);
    handle_runresponse(problemdiv, testresponse);
}

/** Given a response object (JSON-parsed object), displays the result of the
 * test to the user. This modifies the given problemdiv's children.
 */
function handle_runresponse(problemdiv, runresponse)
{
    var runoutput = problemdiv.getElementsByTagName("textarea")[1];
    dom_removechildren(runoutput);
    runoutput.appendChild(document.createTextNode(runresponse.stdout));
}

/** User clicks "Submit" button. Do an Ajax call and run the test.
 * problemid: "id" of the problem's div element.
 * filename: Filename of the problem's XML file (used to identify the problem
 *     when interacting with the server).
 */
function submitproblem(problemid, filename)
{
    /* Get the source code the student is submitting */
    var problemdiv = document.getElementById(problemid);
    var problembox = problemdiv.getElementsByTagName("textarea")[0];
    var code = problembox.value;

    var args = {"code": code, "problem": filename, "action": "test"};

    /* Send the form as multipart/form-data, since we are sending a whole lump
     * of Python code, it should be treated like a file upload. */
    var xhr = ajax_call("tutorialservice", "", args, "POST",
        "multipart/form-data");
    var testresponse = JSON.parse(xhr.responseText);
    handle_testresponse(problemdiv, testresponse);
}

/** Given a problem div, return the testoutput div which is its child.
 * (The div which is its child whose class is "testoutput".
 */
function get_testoutput(problemdiv)
{
    var childs = problemdiv.childNodes;
    var i;
    var testoutput;
    for (i=0; i<childs.length; i++)
        if (childs[i].nodeType == problemdiv.ELEMENT_NODE &&
            childs[i].getAttribute("class") == "testoutput")
            return childs[i];
    return null;
}

/** Given a response object (JSON-parsed object), displays the result of the
 * test to the user. This modifies the given problemdiv's children.
 */
function handle_testresponse(problemdiv, testresponse)
{
    var testoutput = get_testoutput(problemdiv);
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
        ul.appendChild(create_response_item("critical",
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
            fail_li = create_response_item("fail", testcase.name);
            ul.appendChild(fail_li);
            /* Create a sub-ul to display the failing cases. */
            case_ul = document.createElement("ul");
            fail_li.appendChild(case_ul);
            case_ul.appendChild(create_response_item("exception",
                testcase.exception.name, testcase.exception.detail));
        }
        else if (testcase.passed)
        {
            /* All parts of the test case passed. Just report the overall case
             * passing. */
            ul.appendChild(create_response_item("pass", testcase.name));
        }
        else
        {
            var fail_li = create_response_item("fail", testcase.name);
            ul.appendChild(fail_li);
            /* Create a sub-ul to display the failing cases. */
            case_ul = document.createElement("ul");
            fail_li.appendChild(case_ul);
            
            for (j=0; j<testcase.parts.length; j++)
            {
                var part = testcase.parts[j];
                if (part.passed)
                {
                    case_ul.appendChild(create_response_item("pass",
                        part.description));
                }
                else
                {
                    case_ul.appendChild(create_response_item("fail",
                        part.description, part.error_message));
                }
            }
        }
    }
}

/* DOM creators for test case response elements */

/** Create a <li> element for the result of a test case.
 * type: "pass", "fail", "exception" or "critical"
 * detail should be null for passing cases.
 * For exceptions and crits, "desc" is the exception name,
 * detail is the message.
 */
function create_response_item(type, desc, detail)
{
    var crit = false;
    if (type == "critical")
    {
        /* Crits look like exceptions, but are slightly different */
        crit = true;
        type = "exception";
    }
    var li = document.createElement("li");
    li.setAttribute("class", type);
    var b = document.createElement("b");
    var text = type[0].toUpperCase() + type.substr(1) + ":";
    b.appendChild(document.createTextNode(text));
    li.appendChild(b);
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
