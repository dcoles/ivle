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

var server_key;

/* Begin religious debate (tabs vs spaces) here: */
/* (This string will be inserted in the console when the user presses the Tab
 * key) */
TAB_STRING = "    ";

/* Console DOM objects */
console_body = null;
console_filler = null;

windowpane_mode = false;
server_started = false;

/* Starts the console server, if it isn't already.
 * This can be called any number of times - it only starts the one server.
 * This is a separate step from console_init, as the server is only to be
 * started once the first command is entered.
 * Does not return a value. Writes to global variables
 * server_host, and server_port.
 */
function start_server()
{
    if (server_started) return;
    var xhr = ajax_call("consoleservice", "start", {}, "POST");
    var json_text = xhr.responseText;
    server_key = JSON.parse(json_text);
    server_started = true;
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
    /* If there is no console body, don't worry.
     * (This lets us import console.js even on pages without a console box */
    if (console_body == null) return;
    console_filler = document.getElementById("console_filler");
    if (windowpane)
    {
        windowpane_mode = true;
        console_minimize();
    }
    /* TEMP: Start the server now.
     * Ultimately we want the server to start only when a line is typed, but
     * it currently does it asynchronously and doesn't start in time for the
     * first line. */
    start_server();
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
    /* Focus the input box by default */
    document.getElementById("console_inputText").focus()
}

/* current_text is the string currently on the command line.
 * If non-empty, it will be stored at the bottom of the history.
 */
function historyUp(current_text)
{
    /* Remember the changes made to this item */
    this.edited[this.cursor] = current_text;
    if (this.cursor > 0)
    {
        this.cursor--;
    }
    this.earliestCursor = this.cursor;
}

function historyDown(current_text)
{
    /* Remember the changes made to this item */
    this.edited[this.cursor] = current_text;
    if (this.cursor < this.items.length - 1)
    {
        this.cursor++;
    }
}

function historyCurr()
{
    return this.edited[this.cursor];
}

function historySubmit(text)
{
    /* Copy the selected item's "edited" version over the permanent version of
     * the last item. */
    this.items[this.items.length-1] = text;
    /* Add a new blank item */
    this.items[this.items.length] = "";
    this.cursor = this.items.length-1;
    /* Blow away all the edited versions, replacing them with the existing
     * items set.
     * Not the whole history - just start from the earliest edited one.
     * (This avoids slowdown over extended usage time).
     */
    for (var i=this.earliestCursor; i<=this.cursor; i++)
        this.edited[i] = this.items[i];
    this.earliestCursor = this.cursor;
}

function historyShow()
{
    var res = "";
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

/* How history works
 * This is a fairly complex mechanism due to complications when editing
 * history items. We store two arrays. "items" is the permanent history of
 * each item. "edited" is a "volatile" version of items - the edits made to
 * the history between now and last time you hit "enter".
 * This is because the user can go back and edit any of the previous items,
 * and the edits are remembered until they hit enter.
 *
 * When hitting enter, the "edited" version of the currently selected item
 * replaces the "item" version of the last item in the list.
 * Then a new blank item is created, for the new line of input.
 * Lastly, all the "edited" versions are replaced with their stable versions.
 *
 * Cursor never points to an invalid location.
 */
function History()
{
    this.items = new Array("");
    this.edited = new Array("");
    this.cursor = 0;
    this.earliestCursor = 0;
    this.up = historyUp;
    this.down = historyDown;
    this.curr = historyCurr;
    this.submit = historySubmit;
    this.show = historyShow;
}

var hist = new History();

/** Send a line of text to the Python server, wait for its return, and react
 * to its response by writing to the output box.
 * Also maximize the console window if not already.
 */
function console_enter_line(inputline, which)
{
    /* Start the server if it hasn't already been started */
    start_server();
    var args = {"key": server_key, "text":inputline};
    var xmlhttp = ajax_call("consoleservice", which, args, "POST");

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
        console_enter_line(inp.value, "chat");
        hist.submit(inp.value);
        inp.value = hist.curr();
        break;
    case 38:                /* Up arrow */
        hist.up(inp.value);
        inp.value = hist.curr();
        break;
    case 40:                /* Down arrow */
        hist.down(inp.value);
        inp.value = hist.curr();
        break;
    }
}
