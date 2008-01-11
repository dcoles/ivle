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
 * \return DOM Element object.
 */
function dom_make_text_elem(tagname, text)
{
    var elem = document.createElement(tagname);
    elem.appendChild(document.createTextNode(text));
    return elem;
}

/** Creates a DOM element with hyperlinked text inside it.
 * \param tagname String. Name of the element's tag (eg. "p").
 * \param text String. Text to be placed inside the element.
 * \param href String. URL the text will link to. This is a raw string,
 *  it will automatically be URL-encoded.
 * \param onclick Optional string. Will be set as the "onclick" attribute
 *  of the "a" element.
 * \return DOM Element object.
 */
function dom_make_link_elem(tagname, text, href, onclick)
{
    var elem = document.createElement(tagname);
    var link = document.createElement("a");
    link.setAttribute("href", encodeURI(href));
    if (onclick != null)
        link.setAttribute("onclick", onclick);
    link.appendChild(document.createTextNode(text));
    elem.appendChild(link);
    return elem;
}

/** Converts a list of directories into a path name, with a slash at the end.
 * \param pathlist List of strings.
 * \return String.
 */
function pathlist_to_path(pathlist)
{
    ret = "";
    for (var i=0; i<pathlist.length; i++)
    {
        ret += pathlist[i] + "/";
    }
    return ret;
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
 * The args strings are decoded from URL encoding form. Other strings are left
 * in raw URL form.
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
        url = url.substr(index+1);
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
                arg_key = decodeURI(arg_str.substr(0, index));
                arg_val = decodeURI(arg_str.substr(index+1));
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

/** Given an object exactly of the form described for the output of parseurl,
 * returns a URL string built from those parameters.
 * parseurl and buildurl are strict inverses of each other.
 * Note that either query_string or args may be supplied. If both are
 * supplied, query_string is preferred (because it keeps the argument order).
 * If you take a url from parseurl, modify args, and pass to buildurl,
 * you need to set query_string to null to use the new args.
 * \param obj Object as returned by parseurl.
 * \return String, a URL.
 */
function buildurl(obj)
{
    var url = "";
    var query_string = null;

    if (!("scheme" in obj) || obj.scheme != null)
        url = obj.scheme.toString() + "://";
    if (!("server_name" in obj) || obj.server_name != null)
        url += obj.server_name.toString();
    if (!("server_port" in obj) || obj.server_port != null)
        url += ":" + obj.server_port.toString();
    if (!("path" in obj) || obj.path != null)
    {
        var path = obj.path.toString();
        if (path.length > 0 && path[0] != "/")
            path = "/" + path;
        url += path;
    }
    if (!("query_string" in obj) || obj.query_string != null)
        query_string = obj.query_string.toString();
    else if (!("args" in obj) || obj.args != null)
    {
        query_string = "";
        var arg_val;
        for (var arg_key in obj.args)
        {
            arg_val = obj.args[arg_key];
            if (arg_val instanceof Array)
                for (var i=0; i<arg_val.length; i++)
                    query_string += "&" + encodeURI(arg_key) + "=" +
                        encodeURI(arg_val[i]);
            else
                query_string += "&" + encodeURI(arg_key) + "=" +
                    encodeURI(arg_val);
   
        }
        if (query_string == "")
            query_string = null;
        else
            /* Drop the first "&" */
            query_string = query_string.substr(1);
    }

    if (query_string != null)
        url += "?" + query_string;

    return url;
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
