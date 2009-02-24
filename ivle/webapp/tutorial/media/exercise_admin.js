/* IVLE - Informatics Virtual Learning Environment
 * Copyright (C) 2007-2009 The University of Melbourne
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
 * Author: Nick Chadwick
 */

function show_suite(suite)
{

  var suite_div = document.getElementById('suite_data_' + suite);
  var suite_header = document.getElementById('suite_header_' + suite);
  
  suite_div.style.display = 'block';
  suite_header.setAttribute('onclick', "hide_suite('" + suite + "')");

}

function hide_suite(suite)
{

  var suite_div = document.getElementById('suite_data_' + suite);
  var suite_header = document.getElementById('suite_header_' + suite);

  suite_div.style.display = 'none';
  suite_header.setAttribute('onclick', "show_suite('" + suite + "')");
}

function show_variables(suite)
{

  var variables_div = document.getElementById('variables_' + suite);
  var variables_header = document.getElementById('variables_header_' + suite);
  
  variables_div.style.display = 'block';
  variables_header.setAttribute('onclick', "hide_variables('" + suite + "')");

}

function hide_variables(suite)
{

  var variables_div = document.getElementById('variables_' + suite);
  var variables_header = document.getElementById('variables_header_' + suite);

  variables_div.style.display = 'none';
  variables_header.setAttribute('onclick', "show_variables('" + suite + "')");

}

function show_cases(suite)
{

  var cases_div = document.getElementById('test_cases_' + suite);
  var cases_header = document.getElementById('cases_header_' + suite);
  
  cases_div.style.display = 'block';
  cases_header.setAttribute('onclick', "hide_cases('" + suite + "')");

}

function hide_cases(suite)
{

  var cases_div = document.getElementById('test_cases_' + suite);
  var cases_header = document.getElementById('cases_header_' + suite);

  cases_div.style.display = 'none';
  cases_header.setAttribute('onclick', "show_cases('" + suite + "')");

}

function show_case(suite)
{

  var case_div = document.getElementById('test_case_' + suite);
  var case_header = document.getElementById('case_header_' + suite);
  
  case_div.style.display = 'block';
  case_header.setAttribute('onclick', "hide_case('" + suite + "')");

}

function hide_case(suite)
{

  var case_div = document.getElementById('test_case_' + suite);
  var case_header = document.getElementById('case_header_' + suite);

  case_div.style.display = 'none';
  case_header.setAttribute('onclick', "show_case('" + suite + "')");

}
