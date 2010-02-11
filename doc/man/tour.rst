.. IVLE - Informatics Virtual Learning Environment
   Copyright (C) 2007-2010 The University of Melbourne

.. This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

.. This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

.. You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

.. _ivle-tour:

**************
A tour of IVLE
**************

This page is designed to give a brief overview of IVLE, from a users point of
view (including administrator and lecturer users). Here we assume that you
have :ref:`set up a fresh copy of IVLE <ref-install>` and :ref:`installed the
sample data <sample-data>`. This page refers to the sample data specifically.
If you are just using an existing installation of IVLE, it might still make a
bit of sense, but your mileage may vary.

We will take the tour in three stages: first as a student, then as a lecturer,
and finally as an administrator.

A student's view
================

Begin by logging into IVLE as a student (username: 'studenta', password:
'password').

Files
-----

You will see the IVLE home screen, which displays the subjects you are
enrolled in, and your files for each subject. Along the top is the blue bar
which is always visible in IVLE. Clicking the IVLE logo always returns you to
the home screen.

The user "studenta" is enrolled in several subjects, and has several files
already in her Subversion repository, but they aren't immediately accessible.

First, click all of the "Checkout" buttons, to check out the Subversion
repositories. Now you can explore the sample files, for example, in the
"stuff" directory.

Go into the "stuff" directory and left-click the file "hello.py". This will
open the build-in text editor, which lets you modify the file. Along the top,
there is a button marked "Serve". Clicking this will *run* the Python code as
a CGI application -- this should open a new window which reads "Hello,
world!". You can also click "Run", which will run the program in the built-in
Python console (which pops up from the bottom of the screen). This will be
much uglier, printing the CGI output.

* "Serve" runs Python programs as CGI applications, showing their web output.
* "Run" runs Python programs as command-line applications.

Note that you can also use the console at the bottom of the screen as a
generic Python console, whenever you wish.

You can also serve other files, such as HTML files (try "Welcome to
IVLE.html"). This will just present them as normal web pages.

Files also have full Subversion histories. If you click on a file in the file
view (such as "hello.py"), and go to More Actions -> Subversion -> View Log,
you will see the history of a file, and be able to "select" then view a "diff"
of the file. If you edit a file, you need to commit it (More Actions ->
Subversion -> Commit). If you create a new file (More Actions -> Directory
actions -> New file), you need to add it (More Actions -> Subversion -> Add),
then commit.

Submissions
-----------

This student has already completed a project, and is ready to submit it. Go
into the Intermediate Ivle -> mywork directory. Select "phase1.html" and
choose More Actions -> Publishing -> Submit. This takes you to the Submit
Project screen.

Choose to submit to Phase 1, and click Submit Project.

If you go into the Intermediate Ivle -> group1 directory, you will be able to
make a group submission to Phase 2 (which is a group project). Note that the
Phase 3 submission has already closed.
Also note that the file here ("phase2.html") was edited by studenta and
studentb collaboratively, as you can see in the project's revision log.

Worksheets
----------

Click on Intermediate Ivle -> Subject Home from the home screen (or, from the
IVLE pulldown menu, choose Subjects and select Intermediate Ivle). There is
one worksheet, Worksheet Basics. Clicking this takes you to the worksheet,
where students are challenged by Python questions.

After reading the worksheet, attempt the simple programming question, which is
to write a factorial program.

A sample solution follows::

 def fac(n):
     if n == 0:
         return 1
     else:
         return n * fac(n-1)
 
 def main():
     f = int(raw_input())
     print fac(f)

First, click Submit, and note that the system automatically runs some test
cases, all of which fail. Now paste the solution to :func:`fac` (but not
:func:`main`). Clicking Submit again shows some test cases pass, but not all.
Finally, paste the solution to :func:`main`, and click Submit again. This
time, you will pass the test.

Note that you can also click "Run", and it will execute your solution in the
Python console. This doesn't cost you an "attempt", nor does it run the test
cases. It just lets you test it out for yourself before making an official
submission.

Back on the subject page, you will notice that the exercise appears complete,
and you have been awarded some marks.

A lecturer's view
=================

Log into IVLE as a lecturer (username: 'lecturer', password: 'password').

.. warning::
   To be written.

An administrator's view
=======================

Log into IVLE as an admin (username: 'admin', password: 'password').

.. warning::
   To be written.
