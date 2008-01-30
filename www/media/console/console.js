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
 * Module: Console (Client-side JavaScript)
 * Author: Tom Conway, Matt Giuca
 * Date: 30/1/2008
 */

digest_constant = "hello";

var server_host;
var server_port;
var server_magic;

/* Begin religious debate (tabs vs spaces) here: */
/* (This string will be inserted in the console when the user presses the Tab
 * key) */
TAB_STRING = "    ";

/* Console DOM objects */
console_body = null;
console_filler = null;

windowpane_mode = false;

/* Starts the console server.
 * Returns an object with fields "host", "port", "magic" describing the
 * server.
 */
function start_server()
{
    var xhr = ajax_call("consoleservice", "start", {}, "POST");
    var json_text = xhr.responseText;
    return JSON.parse(json_text);
}

/** Initialises the console. All apps which import console are required to
 * call this function.
 * Optional "windowpane" (bool), if true, will cause the console to go into
 * "window pane" mode which will allow it to be opened and closed, and float
 * over the page.
 * (Defaults to closed).
 */
function console_init(windowpane)
{
    /* Set up the console as a floating pane */
    console_body = document.getElementById("console_body");
    console_filler = document.getElementById("console_filler");
    if (windowpane)
    {
        windowpane_mode = true;
        console_minimize();
    }
    /* Start the server */
    var server_info = start_server();
    server_host = server_info.host;
    server_port = server_info.port;
    server_magic = server_info.magic;
}

/** Hide the main console panel, so the console minimizes to just an input box
 *  at the page bottom. */
function console_minimize()
{
    if (!windowpane_mode) return;
    console_body.setAttribute("class", "windowpane minimal");
    console_filler.setAttribute("class", "windowpane minimal");
}

/** Show the main console panel, so it enlarges out to its full size.
 */
function console_maximize()
{
    if (!windowpane_mode) return;
    console_body.setAttribute("class", "windowpane maximal");
    console_filler.setAttribute("class", "windowpane maximal");
}

/* Below here imported from trunk/console/console.js
 * (Tom Conway)
 */

var magic = 'xyzzy';

function historyUp()
{
    if (this.cursor >= 0)
    {
        this.cursor--;
    }
}

function historyDown()
{
    if (this.cursor < this.items.length)
    {
        this.cursor++;
    }
}

function historyCurr()
{
    if (this.cursor < 0 || this.cursor >= this.items.length)
    {
        return "";
    }
    return this.items[this.cursor];
}

function historyAdd(text)
{
    this.items[this.items.length] = text;
    this.cursor = this.items.length;
}

function historyShow()
{
    var res = "";
    if (this.cursor == -1)
    {
        res += "[]";
    }
    for (var i = 0; i < this.items.length; i++)
    {
        if (i == this.cursor)
        {
            res += "["
        }
        res += this.items[i].toString();
        if (i == this.cursor)
        {
            res += "]"
        }
        res += " "
    }
    if (this.cursor == this.items.length)
    {
        res += "[]";
    }
    return res;
}

function History()
{
    this.items = new Array();
    this.cursor = -1;
    this.up = historyUp;
    this.down = historyDown;
    this.curr = historyCurr;
    this.add = historyAdd;
    this.show = historyShow;
}

var hist = new History();

/** Send a line of text to the Python server, wait for its return, and react
 * to its response by writing to the output box.
 * Also maximize the console window if not already.
 */
function console_enter_line(inputline)
{
    var digest = hex_md5(inputline + magic);
    var args = {"host": server_host, "port": server_port,
                    "digest":digest, "text":inputline};
    var xmlhttp = ajax_call("consoleservice", "chat", args, "POST");

    var res = JSON.parse(xmlhttp.responseText);
    var output = document.getElementById("console_output");
    {
        var pre = document.createElement("pre");
        pre.setAttribute("class", "inputMsg");
        pre.appendChild(document.createTextNode(inputline + "\n"));
        output.appendChild(pre);
    }
    if (res.hasOwnProperty('okay'))
    {
        // Success!
        // print out the output (res.okay[0])
        var pre = document.createElement("pre");
        pre.setAttribute("class", "outputMsg");
        pre.appendChild(document.createTextNode(res.okay[0]));
        output.appendChild(pre);
        // print out the return value (res.okay[1])
        if (res.okay[1])
        {
            var pre = document.createElement("pre");
            pre.setAttribute("class", "outputMsg");
            pre.appendChild(document.createTextNode(res.okay[1] + "\n"));
            output.appendChild(pre);
        }
        // set the prompt to >>>
        var prompt = document.getElementById("console_prompt");
        prompt.replaceChild(document.createTextNode(">>> "), prompt.firstChild);
    }
    else if (res.hasOwnProperty('exc'))
    {
        // Failure!
        // print out any output that came before the error
        if (res.exc[0].length > 0)
        {
            var pre = document.createElement("pre");
            pre.setAttribute("class", "outputMsg");
            pre.appendChild(document.createTextNode(res.exc[0]));
            output.appendChild(pre);
        }

        // print out the error message (res.exc)
        var pre = document.createElement("pre");
        pre.setAttribute("class", "errorMsg");
        pre.appendChild(document.createTextNode(res.exc[1]));
        output.appendChild(pre);
    }
    else if (res.hasOwnProperty('more'))
    {
        // Need more input, so set the prompt to ...
        var prompt = document.getElementById("console_prompt");
        prompt.replaceChild(document.createTextNode("... "), prompt.firstChild);
    }
    else {
        // assert res.hasOwnProperty('input')
        var prompt = document.getElementById("console_prompt");
        prompt.replaceChild(document.createTextNode("+++ "), prompt.firstChild);
    }
    /* Open up the console so we can see the output */
    console_maximize();
}

function catch_input(key)
{
    var inp = document.getElementById('console_inputText');
    switch (key)
    {
    case 9:                 /* Tab key */
        var selstart = inp.selectionStart;
        var selend = inp.selectionEnd;
        if (selstart == selend)
        {
            /* No selection, just a carat. Insert a tab here. */
            inp.value = inp.value.substr(0, selstart)
                + TAB_STRING + inp.value.substr(selstart);
        }
        else
        {
            /* Text is selected. Just indent the whole line
             * by inserting a tab at the start */
            inp.value = TAB_STRING + inp.value;
        }
        /* Update the selection so the same characters as before are selected
         */
        inp.selectionStart = selstart + TAB_STRING.length;
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
    case 13:                /* Enter key */
        /* Send the line of text to the server */
        console_enter_line(inp.value);
        hist.add(inp.value);
        inp.value = hist.curr();
        break;
    case 38:                /* Up arrow */
        hist.up();
        inp.value = hist.curr();
        break;
    case 40:                /* Down arrow */
        hist.down();
        inp.value = hist.curr();
        break;
    }
}
