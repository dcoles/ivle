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

interrupted = false;

/* Starts the console server, if it isn't already.
 * This can be called any number of times - it only starts the one server.
 * Note that this is asynchronous. It will return after signalling to start
 * the server, but there is no guarantee that it has been started yet.
 * This is a separate step from console_init, as the server is only to be
 * started once the first command is entered.
 * Does not return a value. Writes to global variables
 * server_host, and server_port.
 *
 * \param callback Function which will be called after the server has been
 * started. No parameters are passed. May be null.
 */
function start_server(callback)
{
    if (server_started)
    {
        callback();
        return;
    }
    var callback1 = function(xhr)
        {
            var json_text = xhr.responseText;
            server_key = JSON.parse(json_text).key;
            server_started = true;
            if (callback != null)
                callback();
        }

    //var current_path;
    if((typeof(current_path) != 'undefined') && current_file)
    {
        // We have a current_path - give a suggestion to the server
        var path;
        if (current_file.isdir)
        {
            // Browser
            path = path_join("/home", current_path);
        }
        else
        {
            // Editor - need to chop off filename
            var tmp_path = current_path.split('/');
            tmp_path.pop();
            path = path_join("/home", tmp_path.join('/'));
        }
        ajax_call(callback1, "console", "service", {"ivle.op": "start", "cwd": path}, "POST");
    }
    else
    {
        // No current_path - let the server decide
        ajax_call(callback1, "console", "service", {"ivle.op": "start"}, "POST");
    }
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

function set_interrupt()
{
    interrupted = true;
}

function clear_output()
{
    var output = document.getElementById("console_output");
    while (output.firstChild)
    {
        output.removeChild(output.firstChild);
    }
}

/** Send a line of text to the Python server, wait for its return, and react
 * to its response by writing to the output box.
 * Also maximize the console window if not already.
 */
function console_enter_line(inputbox, which)
{
    interrupted = false;

    if (typeof(inputbox) == "string")
    {
        var inputline = inputbox;
        inputbox = null;
        var graytimer = null;
    }
    else
    {
        GLOBAL_inputbox = inputbox;     /* For timer */
        var inputline = inputbox.value + "\n";
        var graytimer = setTimeout("GLOBAL_inputbox.setAttribute(\"class\", "
            + "\"disabled\");", 100);
    }
    var output = document.getElementById("console_output");
    {
        // Print ">>>" span
        var span = document.createElement("span");
        span.setAttribute("class", "inputPrompt");
        span.appendChild(document.createTextNode(
              document.getElementById("console_prompt").firstChild.textContent)
                        );
        output.appendChild(span);
        // Print input line itself in a span
        var span = document.createElement("span");
        span.setAttribute("class", "inputMsg");
        span.appendChild(document.createTextNode(inputline));
        output.appendChild(span);
    }
    var args = {"ivle.op": which, "key": server_key, "text":inputline};
    var callback = function(xhr)
        {
            console_response(inputbox, graytimer, inputline, xhr.responseText);
        }
    /* Disable the text box */
    if (inputbox != null)
        inputbox.setAttribute("disabled", "disabled");
    ajax_call(callback, "console", "service", args, "POST");
}

function console_response(inputbox, graytimer, inputline, responseText)
{
    try
    {
        var res = JSON.parse(responseText);
    }
    catch (e)
    {
        alert("An internal error occurred in the python console.");
        return;
    }
    var output = document.getElementById("console_output");
    if (res.hasOwnProperty('okay'))
    {
        // Success!
        if (res.okay)
        {
            output.appendChild(document.createTextNode(res.okay + "\n"));
            output.appendChild(span);
        }
        // set the prompt to >>>
        set_prompt(">>>");
    }
    else if (res.hasOwnProperty('exc'))
    {
        // Failure!
        // print out the error message (res.exc)
        print_error(res.exc);
        
        // set the prompt to >>>
        set_prompt(">>>");
    }
    else if (res.hasOwnProperty('restart') && res.hasOwnProperty('key'))
    {
        // Server has indicated that the console should be restarted
        
        // Get the new key (host, port, magic)
        server_key = res.key;

        // Print a reason to explain why we'd do such a horrible thing
        // (console timeout, server error etc.)
        print_error("Console Restart: " + res.restart);
        
        // set the prompt to >>>
        set_prompt(">>>");
    }
    else if (res.hasOwnProperty('more'))
    {
        // Need more input, so set the prompt to ...
        set_prompt("...");
    }
    else if (res.hasOwnProperty('output'))
    {
        if (res.output.length > 0)
        {
            output.appendChild(document.createTextNode(res.output));
        }
        var callback = function(xhr)
            {
                console_response(inputbox, graytimer,
                                 null, xhr.responseText);
            }
        if (interrupted)
        {
            var kind = "interrupt";
        }
        else
        {
            var kind = "chat";
        }
        var args = {"ivle.op": kind, "key": server_key, "text":''};
        ajax_call(callback, "console", "service", args, "POST");

        // Open up the console so we can see the output
        // FIXME: do we need to maximize here?
        console_maximize();

        /* Auto-scrolling */
        divScroll.activeScroll();

        // Return early, so we don't re-enable the input box.
        return;
    }
    else
    {
        // assert res.hasOwnProperty('input')
        set_prompt("...");
    }

    if (inputbox != null)
    {
        /* Re-enable the text box */
        clearTimeout(graytimer);
        inputbox.removeAttribute("disabled");
        inputbox.removeAttribute("class");
        interrupted = false;
    }

    /* Open up the console so we can see the output */
    console_maximize();
    /* Auto-scrolling */
    divScroll.activeScroll();

    // Focus the input box by default
    document.getElementById("console_output").focus();
    document.getElementById("console_inputText").focus();
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
        var callback = function()
        {
            /* Send the line of text to the server */
            console_enter_line(inp, "chat");
            hist.submit(inp.value);
            inp.value = hist.curr();
        }
        /* Start the server if it hasn't already been started */
        start_server(callback);
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

/** Resets the console by signalling the old console to expire and starting a 
 * new one.
 */
function console_reset()
{
    // FIXME: We show some feedback here - either disable input or at very 
    // least the reset button.

    // Restart the console
    if(!server_started)
    {
        start_server(null);
    }
    else
    {
        xhr = ajax_call(null, "console", "service", {"ivle.op": "restart", "key": server_key}, "POST");
        console_response(null, null, null, xhr.responseText);
    }
}

/** Prints an error line in the console **/
function print_error(error)
{ 
    var output = document.getElementById("console_output");
  
    // Create text block
    var span = document.createElement("span");
    span.setAttribute("class", "errorMsg");
    span.appendChild(document.createTextNode(error + "\n"));
    output.appendChild(span);

    // Autoscroll
    divScroll.activeScroll();
}

/** Sets the prompt text **/
function set_prompt(prompt_text)
{
    var prompt = document.getElementById("console_prompt");
    prompt.replaceChild(document.createTextNode(prompt_text + " "), prompt.firstChild);
}

/**** Following Code modified from ******************************************/
/**** http://radio.javaranch.com/pascarello/2006/08/17/1155837038219.html ***/
/****************************************************************************/
var chatscroll = new Object();

chatscroll.Pane = function(scrollContainerId)
{
    this.scrollContainerId = scrollContainerId;
}

chatscroll.Pane.prototype.activeScroll = function()
{
    var scrollDiv = document.getElementById(this.scrollContainerId);
    var currentHeight = 0;
        
    if (scrollDiv.scrollHeight > 0)
        currentHeight = scrollDiv.scrollHeight;
    else if (scrollDiv.offsetHeight > 0)
        currentHeight = scrollDiv.offsetHeight;

    scrollDiv.scrollTop = currentHeight;

    scrollDiv = null;
}

var divScroll = new chatscroll.Pane('console_output');
