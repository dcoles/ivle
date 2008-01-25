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

/** User clicks "Submit" button. Do an Ajax call and run the test.
 * problemid: "id" of the problem's div element.
 * filename: Filename of the problem's XML file (used to identify the problem
 *     when interacting with the server).
 */
function submitproblem(problemid, filename)
{
    /* Get the source code the student is submitting */
    problemdiv = document.getElementById(problemid);
    problembox = problemdiv.getElementsByTagName("textarea")[0];
    code = problembox.value;
    alert("code = \"" + code + "\"\nproblem = \"" + filename + "\"\n"
        + "action = \"test\"");
}
