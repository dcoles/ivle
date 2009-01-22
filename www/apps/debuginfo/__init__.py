# IVLE
# Copyright (C) 2007-2008 The University of Melbourne
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

# App: debuginfo
# Author: Matt Giuca
# Date: 17/12/2007

# Displays lots of internal information about IVLE's running environment,
# a la phpinfo.
# Important: This application should be removed from a production system.

import os
import cgi

from ivle import util
import ivle.conf

def handle(req):
    """Handler for the Debug Information application."""

    # Set request attributes
    req.content_type = "text/html"
    req.write_html_head_foot = True     # Have dispatch print head and foot

    # Start writing data
    req.write('<div id="ivle_padding">\n')
    req.write("<h2>IVLE Debug Information</h2>\n")

    print_table(req, "System Constants", [
        ("ivle_version", ivle.conf.ivle_version),
        ("prefix", ivle.conf.prefix),
        ("python_site_packages", ivle.conf.python_site_packages),
        ("data_path", ivle.conf.data_path),
        ("log_path", ivle.conf.log_path),
        ("root_dir", ivle.conf.root_dir),
        ("public_host", ivle.conf.public_host),
        ("jail_base", ivle.conf.jail_base),
        ("default_app", ivle.conf.apps.default_app),
        ("public_app", ivle.conf.apps.public_app),
    ])

    print_table(req, "Operating System Variables", [
        ("uid", os.getuid()),
        ("euid", os.geteuid()),
        ("gid", os.getgid()),
        ("egid", os.getegid()),
        ("uname", os.uname()),
    ])

    print_table(req, "Available Applications", ivle.conf.apps.app_url.items())

    print_table(req, "Request Properties", [
        ("method", req.method),
        ("uri", req.uri),
        ("app", req.app),
        ("path", req.path),
        ("user", req.user),
        ("hostname", req.hostname),
    ])

    # Violate encapsulation here to print out the hidden properties
    print_table(req, "Apache (Hidden) Request Properties", [
        ("hostname", req.apache_req.hostname),
        ("method", req.apache_req.method),
        ("unparsed_uri", req.apache_req.unparsed_uri),
        ("parsed_uri", req.apache_req.parsed_uri),
        ("uri", req.apache_req.uri),
        ("filename", req.apache_req.filename),
        ("path_info", req.apache_req.path_info),
    ])

    print_table(req, "Field Storage",
        getfieldvalues(req.get_fieldstorage().items()))
    session = req.get_session()
    print_table(req, "Session Variables", session.items())

    print_table(req, "HTTP Request Headers",
        req.apache_req.headers_in.items())
    print_table(req, "CGI Environment Variables",
        req.get_cgi_environ().items())
    print_table(req, "Server Environment Variables", os.environ.items())

    req.write("<h3>Removal instructions</h3>\n")
    req.write("""<p>In a production environment, debuginfo should be disabled.
    To do this, comment out or remove the debuginfo line of the app_url
    dictionary in ivle/conf/apps.py.</p>
    <p>For extra security, it may be removed completely by deleting the
    apps/debuginfo directory.</p>
</div>
""")

def getfieldvalues(pairs):
    """Given a list of pairs of strings and fields, returns a new list with
    the 2nd elements of each pair modified to be the field's value."""
    if pairs is None: return None
    newlist = []
    for k,v in pairs:
        newlist.append((k,v.value))
    return newlist

def print_table(req, tablename, mapping, head_elem="h3"):
    """Prints an HTML table with a heading.

    mapping: An associative list (a list of pairs). The pairs are printed
    using (str, repr) respectively into the two-column table."""
    req.write("<%s>%s</%s>\n" % (head_elem, tablename, head_elem))
    req.write('<table border="1">\n')
    for (k,v) in mapping:
        req.write("<tr><th>%s</th><td>%s</td></tr>\n" %
                  (cgi.escape(str(k)), cgi.escape(repr(v))))
    req.write("</table>\n")

