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
 * Module: JavaScript Utilities
 * Author: Matt Giuca
 * Date: 11/1/2008
 *
 * Defines some generic JavaScript utility functions.
 */

/* Expects the following variables to have been declared by JavaScript in
 * the HTML generated by the server:
 * - root_dir
 * - public_host
 * - username
 */

/** Removes all children of a given DOM element
 * \param elem A DOM Element. Will be modified.
 */
function dom_removechildren(elem)
{
    while (elem.lastChild != null)
        elem.removeChild(elem.lastChild);
}

/** Creates a DOM element with simple text inside it.
 * \param tagname String. Name of the element's tag (eg. "p").
 * \param text String. Text to be placed inside the element.
 * \param title String, optional. Tooltip for the text.
 *  (Note, title creates a span element around the text).
 * \return DOM Element object.
 */
function dom_make_text_elem(tagname, text, title)
{
    if (text == null) text = "";
    var elem = document.createElement(tagname);
    var textnode;
    if (title == null)
        textnode = document.createTextNode(text);
    else
    {
        textnode = document.createElement("span");
        textnode.setAttribute("title", title);
        textnode.appendChild(document.createTextNode(text));
    }
    elem.appendChild(textnode);
    return elem;
}

/** Creates a DOM element with hyperlinked text inside it.
 * \param tagname String. Name of the element's tag (eg. "p").
 * \param text String. Text to be placed inside the element.
 * \param title String, optional. Sets a tooltip for the link.
 * \param href String. URL the text will link to. This is a raw string,
 *  it will automatically be URL-encoded.
 * \param onclick Optional string. Will be set as the "onclick" attribute
 *  of the "a" element.
 * \param dontencode Optional boolean. If true, will not encode the href.
 *  if including query strings, you must set this to true and use build_url
 *  to escape the URI correctly.
 * \return DOM Element object.
 */
function dom_make_link_elem(tagname, text, title, href, onclick, dontencode)
{
    if (text == null) text = "";
    if (href == null) href = "";
    var elem = document.createElement(tagname);
    var link = document.createElement("a");
    if (dontencode != true)
        href = urlencode_path(href);
    link.setAttribute("href", href);
    if (title != null)
        link.setAttribute("title", title);
    if (onclick != null)
        link.setAttribute("onclick", onclick);
    link.appendChild(document.createTextNode(text));
    elem.appendChild(link);
    return elem;
}

/** Creates a DOM img element. All parameters are optional except src.
 * If alt (compulsory in HTML) is omitted, will be set to "".
 */
function dom_make_img(src, width, height, title, alt)
{
    var img = document.createElement("img");
    img.setAttribute("src", urlencode_path(src));
    if (width != null)
        img.setAttribute("width", width);
    if (height != null)
        img.setAttribute("height", height);
    if (title != null)
        img.setAttribute("title", title);
    if (alt == null) alt = "";
    img.setAttribute("alt", alt);
    return img;
}

/** Given a number of bytes, returns a string representing the file size in a
 * human-readable format.
 * eg. nice_filesize(6) -> "6 bytes"
 *     nice_filesize(81275) -> "79.4 kB"
 *     nice_filesize(13498346) -> "12.9 MB"
 * \param bytes Number of bytes. Must be an integer.
 * \return String.
 */
function nice_filesize(bytes)
{
    if (bytes == null) return "";
    var size;
    if (bytes < 1024)
        return bytes.toString() + " B";
    size = bytes / 1024;
    if (size < 1024)
        return size.toFixed(1) + " kB";
    size = size / 1024;
    if (size < 1024)
        return size.toFixed(1) + " MB";
    size = size / 1024;
    return size.toFixed(1) + " GB";
}

/** Given a URL, returns an object containing a number of attributes
 * describing the components of the URL, similar to CGI request variables.
 * The object has the following attributes:
 * - scheme
 * - server_name
 * - server_port
 * - path
 * - query_string
 * - args
 * The first five of these are strings, which comprise the URL as follows:
 * <scheme> "://" <server_name> ":" <server_port> <path> "?" <query_string>
 * Any of these strings may be set to null if not found.
 *
 * "args" is an object whose attributes are the query_string arguments broken
 * up.
 * Args values are strings for single values, arrays of strings for values
 * whose names appear multiple times.
 * args is never null, though it may be empty.
 *
 * All strings are decoded/unescaped. Reserved characters
 * (; , / ? : @ & = + * $) are not decoded except in args and path.
 *
 * \param url String. A URL. To read from the current browser window, use
 *  window.location.href.
 * \return The above described object.
 */
function parse_url(url)
{
    var obj = {};
    var index;
    var serverpart;
    var args;

    /* Split scheme from rest */
    index = url.indexOf("://");
    if (index < 0)
        obj.scheme = null;
    else
    {
        obj.scheme = url.substr(0, index);
        url = url.substr(index+3);
    }

    /* Split server name/port from rest */
    index = url.indexOf("/");
    if (index < 0)
    {
        serverpart = url;
        url = null;
    }
    else
    {
        serverpart = url.substr(0, index);
        url = url.substr(index);
    }

    /* Split server name from port */
    index = serverpart.indexOf(":");
    if (index < 0)
    {
        obj.server_name = serverpart;
        obj.server_port = null;
    }
    else
    {
        obj.server_name = serverpart.substr(0, index);
        obj.server_port = serverpart.substr(index+1);
    }

    /* Split path from query string */
    if (url == null)
    {
        obj.path = null;
        obj.query_string = null;
    }
    else
    {
        index = url.indexOf("?");
        if (index < 0)
        {
            obj.path = url;
            obj.query_string = null;
        }
        else
        {
            obj.path = url.substr(0, index);
            obj.query_string = url.substr(index+1);
        }
    }
    obj.path = decodeURIComponent(obj.path);

    /* Split query string into arguments */
    args = {};
    if (obj.query_string != null)
    {
        var args_strs = obj.query_string.split("&");
        var arg_str;
        var arg_key, arg_val;
        for (var i=0; i<args_strs.length; i++)
        {
            arg_str = args_strs[i];
            index = arg_str.indexOf("=");
            /* Ignore malformed args */
            if (index >= 0)
            {
                arg_key = decodeURIComponent(arg_str.substr(0, index));
                arg_val = decodeURIComponent(arg_str.substr(index+1));
                if (arg_key in args)
                {
                    /* Collision - make an array */
                    if (args[arg_key] instanceof Array)
                        args[arg_key][args[arg_key].length] = arg_val;
                    else
                        args[arg_key] = [args[arg_key], arg_val];
                }
                else
                    args[arg_key] = arg_val;
            }
        }
    }
    obj.args = args;

    return obj;
}

/** Builds a query_string from an args object. Encodes the arguments.
 * \param args Args object as described in parse_url.
 * \return Query string portion of a URL.
 */
function make_query_string(args)
{
    var query_string = "";
    var arg_val;
    for (var arg_key in args)
    {
        arg_val = args[arg_key];
        if (arg_val instanceof Array)
            for (var i=0; i<arg_val.length; i++)
                query_string += "&" + encodeURIComponent(arg_key) + "=" +
                    encodeURIComponent(arg_val[i]);
        else
            query_string += "&" + encodeURIComponent(arg_key) + "=" +
                encodeURIComponent(arg_val);
    }
    if (query_string != "")
        /* Drop the first "&" */
        query_string = query_string.substr(1);

    return query_string;
}

/** Given an object exactly of the form described for the output of parseurl,
 * returns a URL string built from those parameters. The URL is properly
 * encoded.
 * parseurl and buildurl are strict inverses of each other.
 * Note that either query_string or args may be supplied. If both are
 * supplied, query_string is preferred (because it keeps the argument order).
 * If you take a url from parseurl, modify args, and pass to buildurl,
 * you need to set query_string to null to use the new args.
 * \param obj Object as returned by parseurl.
 * \return String, a URL.
 */
function build_url(obj)
{
    var url = "";
    var query_string = null;

    if (("scheme" in obj) && obj.scheme != null)
        url = obj.scheme.toString() + "://";
    if (("server_name" in obj) && obj.server_name != null)
        url += obj.server_name.toString();
    if (("server_port" in obj) && obj.server_port != null)
        url += ":" + obj.server_port.toString();
    if (("path" in obj) && obj.path != null)
    {
        var path = urlencode_path(obj.path.toString());
        if (url.length > 0 && path.length > 0 && path.charAt(0) != "/")
            path = "/" + path;
        url += path;
    }
    if (("query_string" in obj) && obj.query_string != null)
        query_string = encodeURI(obj.query_string.toString());
    else if (("args" in obj) && obj.args != null)
        query_string = make_query_string(obj.args);

    if (query_string != "" && query_string != null)
        url += "?" + query_string;

    return url;
}

/** URL-encodes a path. This is a special case of URL encoding as all
 * characters *except* the slash must be encoded.
 */
function urlencode_path(path)
{
    /* Split up the path, URLEncode each segment with encodeURIComponent,
     * and rejoin.
     */
    var split = path.split('/');
    for (var i=0; i<split.length; i++)
        split[i] = encodeURIComponent(split[i]);
    path = path_join.apply(null, split);
    if (split[0] == "" && split.length > 1) path = "/" + path;
    return path;
}

/** Writes a JSONable object to the cookie under a particular key
 * (JSON encoded and URL encoded).
 */
function write_cookie(key, value)
{
    var sendstr = encodeURIComponent(key) + "="
        + encodeURIComponent(JSON.stringify(value))
        + "; path=" + urlencode_path(root_dir);
    /* This actually just assigns to the key, not replacing the whole cookie
     * as it appears to. */
    document.cookie = sendstr;
}
/** Reads a cookie which has a JSONable object encoded as its value.
 * Returns the object, parsed from JSON.
 */
function read_cookie(key)
{
    var cookies = document.cookie.split(";");
    var checkstart = encodeURIComponent(key) + "=";
    var checklen = checkstart.length;
    for (var i=0; i<cookies.length; i++)
    {
        var cookie = cookies[i];
        while (cookie[0] == ' ')
            cookie = cookie.substr(1);
        if (cookie.substr(0, checklen) == checkstart)
        {
            var valstr = cookie.substr(checklen);
            valstr = decodeURIComponent(valstr);
            return JSON.parse(valstr);
        }
    }
}

/** Given an argument map, as output in the args parameter of the return of
 * parseurl, gets the first occurence of an argument in the URL string.
 * If the argument was not found, returns null.
 * If there was a single argument, returns the argument.
 * If there were multiple arguments, returns the first.
 * \param args Object mapping arguments to strings or arrays of strings.
 * \param arg String. Argument name.
 * \return String.
 */
function arg_getfirst(args, arg)
{
    if (!(arg in args))
        return null;
    var r = args[arg];
    if (r instanceof Array)
        return r[0];
    else
        return r;
}

/** Given an argument map, as output in the args parameter of the return of
 * parseurl, gets all occurences of an argument in the URL string, as an
 * array.
 * If the argument was not found, returns [].
 * Otherwise, returns all occurences as an array, even if there was only one.
 * \param args Object mapping arguments to strings or arrays of strings.
 * \param arg String. Argument name.
 * \return Array of strings.
 */
function arg_getlist(args, arg)
{
    if (!(arg in args))
        return [];
    var r = args[arg];
    if (r instanceof Array)
        return r;
    else
        return [r];
}

/** Joins one or more paths together. Accepts 1 or more arguments.
 */
function path_join(path1 /*, path2, ... */)
{
    var arg;
    var path = "";
    for (var i=0; i<arguments.length; i++)
    {
        arg = arguments[i];
        if (arg.length == 0) continue;
        if (arg.charAt(0) == '/')
            path = arg;
        else
        {
            if (path.length > 0 && path.charAt(path.length-1) != '/')
                path += '/';
            path += arg;
        }
    }
    return path;
}


/** Builds a multipart_formdata string from an args object. Similar to
 * make_query_string, but it returns data of type "multipart/form-data"
 * instead of "application/x-www-form-urlencoded". This is good for
 * encoding large strings such as text objects from the editor.
 * Should be written with a Content-Type of
 * "multipart/form-data, boundary=<boundary>".
 * All fields are sent with a Content-Type of text/plain.
 * \param args Args object as described in parse_url.
 * \param boundary Random "magic" string which DOES NOT appear in any of
 *  the argument values. This should match the "boundary=" value written to
 *  the Content-Type header.
 * \return String in multipart/form-data format.
 */
function make_multipart_formdata(args, boundary)
{
    var data = "";
    var arg_val;
    /* Mutates data */
    var extend_data = function(arg_key, arg_val)
    {
        /* FIXME: Encoding not supported here (should not matter if we
         * only use ASCII names */
        data += "--" + boundary + "\r\n"
            + "Content-Disposition: form-data; name=\"" + arg_key
            + "\"\r\n\r\n"
            + arg_val + "\r\n";
    }

    for (var arg_key in args)
    {
        arg_val = args[arg_key];
        if (arg_val instanceof Array)
            for (var i=0; i<arg_val.length; i++)
            {
                extend_data(arg_key, arg_val[i]);
            }
        else
            extend_data(arg_key, arg_val);
    }
    /* End boundary */
    data += "--" + boundary + "--\r\n";

    return data;
}

/** Converts a list of directories into a path name, with a slash at the end.
 * \param pathlist List of strings.
 * \return String.
 */
function pathlist_to_path(pathlist)
{
    ret = path_join.apply(null, pathlist);
    if (ret.charAt(ret.length-1) != '/')
        ret += '/';
    return ret;
}

/** Given a path relative to the IVLE root, gives a path relative to
 * the site root.
 */
function make_path(path)
{
    return path_join(root_dir, path);
}

/** Shorthand for make_path(path_join(app, ...))
 * Creates an absolute path for a given path within a given app.
 */
function app_path(app /*,...*/)
{
    return make_path(path_join.apply(null, arguments));
}

/** Generates an absolute URL to a public application
 */
function public_app_path(app /*,...*/)
{
    return location.protocol + "//" + public_host
        + make_path(path_join.apply(null, arguments));
}

/** Given a path, gets the "basename" (the last path segment).
 */
function path_basename(path)
{
    segments = path.split("/");
    if (segments[segments.length-1].length == 0)
        return segments[segments.length-2];
    else
        return segments[segments.length-1];
}

/** Given a string str, determines whether it ends with substr */
function endswith(str, substring)
{
    if (str.length < substring.length) return false;
    return str.substr(str.length - substring.length) == substring;
}

/** Removes all occurences of a value from an array.
 */
Array.prototype.removeall = function(val)
{
    var i, j;
    var arr = this;
    j = 0;
    for (i=0; i<arr.length; i++)
    {
        arr[j] = arr[i];
        if (arr[i] != val) j++;
    }
    arr.splice(j, i-j);
}

/** Shallow-clones an object */
function shallow_clone_object(obj)
{
    o = {};
    for (k in obj)
        o[k] = obj[k];
    return o;
}

/** Returns a new XMLHttpRequest object, in a somewhat browser-agnostic
 * fashion.
 */
function new_xmlhttprequest()
{
    try
    {
        /* Real Browsers */
        return new XMLHttpRequest();
    }
    catch (e)
    {
        /* Internet Explorer */
        try
        {
            return new ActiveXObject("Msxml2.XMLHTTP");
        }
        catch (e)
        {
            try
            {
                return new ActiveXObject("Microsoft.XMLHTTP");
            }
            catch (e)
            {
                throw("Your browser does not support AJAX. "
                    + "IVLE requires a modern browser.");
            }
        }
    }
}

/** Creates a random string of length length,
 * consisting of alphanumeric characters.
 */
var rand_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZ"
               + "abcdefghiklmnopqrstuvwxyz";
function random_string(length)
{
    var str = Array(length);
    var v;
    for (var i=0; i<length; i++)
    {
        v = Math.floor(Math.random() * rand_chars.length);
        str[i] = rand_chars.charAt(v);
    }
    return str.join('');
}

/** Makes an XMLHttpRequest call to the server.
 * Sends the XMLHttpRequest object containing the completed response to a
 * specified callback function.
 *
 * \param callback A callback function. Will be called when the response is
 *      complete. Passed 1 parameter, an XMLHttpRequest object containing the
 *      completed response. If callback is null this is a syncronous request 
 *      otherwise this is an asynchronous request.
 * \param app IVLE app to call (such as "fileservice").
 * \param path URL path to make the request to, within the application.
 * \param args Argument object, as described in parse_url and friends.
 * \param method String; "GET", "POST", "PUT", or "PATCH"
 * \param content_type String, optional.
 *      Defaults to "application/x-www-form-urlencoded".
 */
function ajax_call(callback, app, path, args, method, content_type)
{
    if (!content_type)
        content_type = "application/x-www-form-urlencoded";
    path = app_path(app, path);
    var url;
    /* A random string, for multipart/form-data
     * (This is not checked against anywhere else, it is solely defined and
     * used within this function) */
    var boundary = random_string(20);
    var xhr = new_xmlhttprequest();
    var asyncronous = callback != null;
    if (asyncronous)
    {
        xhr.onreadystatechange = function()
            {
                if (xhr.readyState == 4)
                {
                    callback(xhr);
                }
            }
    }
    if (method == "GET")
    {
        /* GET sends the args in the URL */
        url = build_url({"path": path, "args": args});
        /* open's 3rd argument = true -> asynchronous */
        xhr.open(method, url, asyncronous);
        xhr.send(null);
    }
    else
    {
        /* POST & PUT & PATCH sends the args in the request body */
        url = encodeURI(path);
        xhr.open(method, url, asyncronous);
        var message;
        if (content_type == "multipart/form-data")
        {
            xhr.setRequestHeader("Content-Type",
                "multipart/form-data; boundary=" + boundary);
            message = make_multipart_formdata(args, boundary);
        }
        else if (content_type == "application/x-www-form-urlencoded")
        {
            xhr.setRequestHeader("Content-Type", content_type);
            message = make_query_string(args);
        }
        else if (content_type == "application/json")
        {
            xhr.setRequestHeader("Content-Type", content_type);
            message = JSON.stringify(args);
        }
        else
        {
            xhr.setRequestHeader("Content-Type", content_type);
            message = args;
        }
        xhr.send(message);
    }
    /* Only return the XHR for syncronous requests */
    if (!asyncronous)
    { 
        return xhr;
    }
}

/** Attempts to JSON decodes a response object
 * If a non-200 response or the JSON decode fails then returns null
 */
function decode_response(response)
{
    if (response.status == 200)
    {
        try
        {
            var responseText = response.responseText;
            return JSON.parse(responseText);
        }
        catch (e)
        {
            // Pass
        }
     }
    
     return null;
}
