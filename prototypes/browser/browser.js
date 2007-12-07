/* browser.js
 * Client-side interaction for both file browser and editor.
 * PROOF-OF-CONCEPT ONLY
 *
 * Author: Matt Giuca
 */

var gpathlist;

/* Removes all children of a given element */
function removechildren(elem)
{
    while (elem.lastChild != null)
        elem.removeChild(elem.lastChild);
}

/* Clears all dynamic data from the page, so it can be refilled. */
function clearfiles()
{
    path = document.getElementById("path");
    removechildren(path);
    files = document.getElementById("files");
    removechildren(files);
}

function makebutton(text, action)
{
    button = document.createElement("input");
    button.setAttribute("type", "button");
    button.setAttribute("value", text);
    button.setAttribute("onclick", action);
    return button;
}

/* Makes a TD element with text in it */
function maketd(text)
{
    td = document.createElement("td");
    td.appendChild(document.createTextNode(text));
    return td;
}

function maketdwithlink(text, href, onclick)
{
    td = document.createElement("td");
    link = document.createElement("a");
    link.setAttribute("href", href);
    if (onclick != null)
        link.setAttribute("onclick", onclick);
    link.appendChild(document.createTextNode(text));
    td.appendChild(link);
    return td;
}

/* file is a listing object, with fields as returned by the server. */
function maketdwithactions(file)
{
    td = document.createElement("td");
    if (!file.isdir)
    {
        td.appendChild(makebutton("Delete", "rm(\"" + file.filename + "\")"));
        td.appendChild(makebutton("Rename", "rename(\"" + file.filename + "\")"));
        td.appendChild(makebutton("Edit", "edit(\"" + file.filename + "\")"));
    }
    if (file.svnstatus == "unversioned")
        td.appendChild(makebutton("Add", "svnadd(\"" + file.filename + "\")"));
    else if (file.svnstatus == "added" || file.svnstatus == "modified")
        td.appendChild(makebutton("Commit", "svncommit(\"" + file.filename + "\")"));
    return td;
}

/* Converts a list of directories into a path name, with a slash at the end */
function pathlisttopath(pathlist)
{
    ret = "";
    for each (dir in pathlist)
    {
        ret += dir + "/";
    }
    return ret;
}

function presentpath(pathlist)
{
    path = document.getElementById("path");
    gpathlist = pathlist;
    pathlist = ["home"].concat(pathlist);
    navlist = [];
    home = true;

    /* Create all of the paths */
    for each (dir in pathlist)
    {
        if (home == false)
            navlist.push(dir);
        home = false;
        /* Make an 'a' element */
        link = document.createElement("a");
        link.setAttribute("href", "#");
        link.setAttribute("onclick", "nav(" + JSON.stringify(navlist) + ")");
        link.appendChild(document.createTextNode(dir));
        path.appendChild(link);
        path.appendChild(document.createTextNode("/"));
    }
}

/* Presents a directory listing to the page.
 * pathlist is an array of strings, the names of the directories in the path.
 * listing is a list of objects where each object is a file (containing
 * several fields about the file).
 */
function presentlisting(pathlist, listing)
{
    presentpath(pathlist);
    files = document.getElementById("files");

    /* Create all of the files */
    for each (file in listing)
    {
        /* Make a 'tr' element */
        row = document.createElement("tr");
        if (file.isdir)
        {
            row.appendChild(maketd("dir"));
            navlink = JSON.stringify(navlist.concat([file.filename]));
            navlink = "nav(" + navlink + ")";
            row.appendChild(maketdwithlink(file.filename, "#", navlink));
        }
        else
        {
            row.appendChild(maketd("file"));
            row.appendChild(maketd(file.filename));
        }
        row.appendChild(maketd(file.svnstatus));
        row.appendChild(maketd(file.size));
        row.appendChild(maketd(file.mtime));
        row.appendChild(maketdwithactions(file));
        files.appendChild(row);
    }
}

/* AJAX */

function obj_to_query_string(pagename, obj)
{
    var hadone = false;
    qs = pagename;
    for (key in obj)
    {
        vals = obj[key];
        // vals can be an array, to make multiple args with the same name
        // To handle this, make non-array objects into an array, then loop
        if (!(vals instanceof Array))
            vals = [vals];
        for each (val in vals)
        {
            if (hadone == false)
            {
                qs += "?";
                hadone = true;
            }
            else
                qs += "&";
            qs += encodeURI(key) + "=" + encodeURI(val);
        }
    }
    return qs;
}

/* ACTIONS */

function nav(pathlist)
{
    gpathlist = pathlist;
    refresh();
}

function refresh()
{ 
    path = pathlisttopath(gpathlist);
    url = obj_to_query_string("files.py/ls", {"path" : path});
    var xmlhttp =  new XMLHttpRequest();
        // false -> SYNCHRONOUS (wait for response)
        // (No need for a callback function)
    xmlhttp.open("GET", url, false);
    xmlhttp.send("");
    listing = JSON.parse(xmlhttp.responseText);
    if (listing == null)
        alert("An error occured");
    else if ("error" in listing)
        alert("Error: " + listing.error);
    else
    {
        clearfiles();
        presentlisting(gpathlist, listing);
    }
}

function rm(filename)
{
    path = pathlisttopath(gpathlist);
    url = obj_to_query_string("files.py/rm",
        {"path" : path, "filename" : filename});
    var xmlhttp =  new XMLHttpRequest();
        // false -> SYNCHRONOUS (wait for response)
        // (No need for a callback function)
    xmlhttp.open("GET", url, false);
    xmlhttp.send("");
    listing = JSON.parse(xmlhttp.responseText);
    if (listing == null)
        alert("An error occured");
    else if ("error" in listing)
        alert("Error: " + listing.error);
    else
    {
        clearfiles();
        presentlisting(gpathlist, listing);
    }
}

function rename(fromfilename)
{
    tofilename = prompt("Rename file \"" + fromfilename + "\" to?");
    path = pathlisttopath(gpathlist);
    url = obj_to_query_string("files.py/rename",
        {"path" : path, "fromfilename" : fromfilename,
        "tofilename" : tofilename});
    var xmlhttp =  new XMLHttpRequest();
        // false -> SYNCHRONOUS (wait for response)
        // (No need for a callback function)
    xmlhttp.open("GET", url, false);
    xmlhttp.send("");
    listing = JSON.parse(xmlhttp.responseText);
    if (listing == null)
        alert("An error occured");
    else if ("error" in listing)
        alert("Error: " + listing.error);
    else
    {
        clearfiles();
        presentlisting(gpathlist, listing);
    }
}

/* filenames is a list of filenames */
function svnadd(filenames)
{
    path = pathlisttopath(gpathlist);
    url = obj_to_query_string("files.py/svnadd",
        {"path" : path, "filename" : filenames});
    var xmlhttp =  new XMLHttpRequest();
        // false -> SYNCHRONOUS (wait for response)
        // (No need for a callback function)
    xmlhttp.open("GET", url, false);
    xmlhttp.send("");
    listing = JSON.parse(xmlhttp.responseText);
    if (listing == null)
        alert("An error occured");
    else if ("error" in listing)
        alert("Error: " + listing.error);
    else
    {
        clearfiles();
        presentlisting(gpathlist, listing);
    }
}

/* filenames is a list of filenames */
function svncommit(filenames)
{
    path = pathlisttopath(gpathlist);
    url = obj_to_query_string("files.py/svncommit",
        {"path" : path, "filename" : filenames});
    var xmlhttp =  new XMLHttpRequest();
        // false -> SYNCHRONOUS (wait for response)
        // (No need for a callback function)
    xmlhttp.open("GET", url, false);
    xmlhttp.send("");
    listing = JSON.parse(xmlhttp.responseText);
    if (listing == null)
        alert("An error occured");
    else if ("error" in listing)
        alert("Error: " + listing.error);
    else
    {
        clearfiles();
        presentlisting(gpathlist, listing);
    }
}

function svncommitall()
{
    path = pathlisttopath(gpathlist);
    url = obj_to_query_string("files.py/svncommit",
        {"path" : path, "commitall" : "yes"});
    var xmlhttp =  new XMLHttpRequest();
        // false -> SYNCHRONOUS (wait for response)
        // (No need for a callback function)
    xmlhttp.open("GET", url, false);
    xmlhttp.send("");
    listing = JSON.parse(xmlhttp.responseText);
    if (listing == null)
        alert("An error occured");
    else if ("error" in listing)
        alert("Error: " + listing.error);
    else
    {
        clearfiles();
        presentlisting(gpathlist, listing);
    }
}

function newfile()
{
    window.location = "edit.html";
}

function edit(filename)
{
    window.location = "edit.html?filename="
        + pathlisttopath(gpathlist) + filename;
}

function savefile()
{
    filename = document.getElementById("filename").value;
    data = document.getElementById("data").value;
    url = obj_to_query_string("files.py/putfile",
        {"path" : "", "filename" : filename, "data" : data});
    var xmlhttp =  new XMLHttpRequest();
        // false -> SYNCHRONOUS (wait for response)
        // (No need for a callback function)
    xmlhttp.open("GET", url, false);
    xmlhttp.send("");
    listing = JSON.parse(xmlhttp.responseText);
    if (listing == null)
        alert("An error occured");
    else if ("error" in listing)
        alert("Error: " + listing.error);
}

function loadfile()
{
    filename = document.getElementById("filename").value;
    if (filename == null || filename == "")
        return;
    url = obj_to_query_string("files.py/getfile",
        {"path" : "", "filename" : filename});
    var xmlhttp =  new XMLHttpRequest();
        // false -> SYNCHRONOUS (wait for response)
        // (No need for a callback function)
    xmlhttp.open("GET", url, false);
    xmlhttp.send("");
    document.getElementById("data").value = xmlhttp.responseText;
}

/* Called on page load */
function init_browser()
{
    gpathlist = [];
    refresh();
}

function init_edit()
{
    document.getElementById("filename").value = getURLParam("filename");
    loadfile();
}

/* BORROWED CODE */

/* http://www.11tmr.com/11tmr.nsf/d6plinks/MWHE-695L9Z */
function getURLParam(strParamName){
  var strReturn = "";
  var strHref = window.location.href;
  if ( strHref.indexOf("?") > -1 ){
    var strQueryString = strHref.substr(strHref.indexOf("?"));
    var aQueryString = strQueryString.split("&");
    for ( var iParam = 0; iParam < aQueryString.length; iParam++ ){
      if (
aQueryString[iParam].indexOf(strParamName.toLowerCase() + "=") > -1 ){
        var aParam = aQueryString[iParam].split("=");
        strReturn = aParam[1];
        break;
      }
    }
  }
  return decodeURI(strReturn);
}
