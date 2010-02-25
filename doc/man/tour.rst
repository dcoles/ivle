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

Begin by logging into IVLE as a student (username: ``studenta``, password:
``password``).

Files
-----

You will see the IVLE home screen, which displays the subjects you are
enrolled in, and your files for each subject. Along the top is the blue bar
which is always visible in IVLE. Clicking the IVLE logo always returns you to
the home screen.

The user ``studenta`` is enrolled in several subjects, and has several files
already in her Subversion repository, but they aren't immediately accessible.

First, click all of the *Checkout* buttons, to check out the Subversion
repositories. Now you can explore the sample files, for example, in the
``stuff`` directory.

Go into the ``stuff`` directory and left-click the file ``hello.py``. This will
open the build-in text editor, which lets you modify the file. Along the top,
there is a button marked *Serve*. Clicking this will *run* the Python code as
a CGI application -- this should open a new window which reads "Hello,
world!". You can also click *Run*, which will run the program in the built-in
Python console (which pops up from the bottom of the screen). This will be
much uglier, printing the CGI output.

* *Serve* runs Python programs as CGI applications, showing their web output.
* *Run* runs Python programs as command-line applications.

Note that you can also use the console at the bottom of the screen as a
generic Python console, whenever you wish.

You can also serve other files, such as HTML files (try ``Welcome to
IVLE.html``). This will just present them as normal web pages.

Files also have full Subversion histories. If you click on a file in the file
view (such as ``hello.py``), and go to *More Actions ‣ Subversion ‣ View Log*,
you will see the history of a file, and be able to "select" then view a "diff"
of the file. If you edit a file, you need to commit it (*More Actions ‣
Subversion ‣ Commit*). If you create a new file (*More Actions ‣ Directory
actions ‣ New file*), you need to add it (*More Actions ‣ Subversion ‣ Add*),
then commit.

Submissions
-----------

This student has already completed a project, and is ready to submit it. Go
into the *Intermediate IVLE ‣ mywork* directory. Select ``phase1.html`` and
choose *More Actions ‣ Publishing ‣ Submit*. This takes you to the Submit
Project screen.

Choose to submit to Phase 1, and click *Submit Project*. You should see a page
telling you the submission was successful, with a link to *Verify*. Verify
shows you exactly which files were submitted, and their contents at the time
of submission (if the files have changed since then, you'll still see the
submitted version). You should verify after each submission -- you can verify
any submitted project from the subject page.

If you go into the *Intermediate IVLE ‣ group1* directory, you will be able
to make a group submission to Phase 2 (which is a group project). Note that
the Phase 3 submission has already closed.
Also note that the file here (``phase2.html``) was edited by studenta and
studentb collaboratively, as you can see in the project's revision log.

Worksheets
----------

Click on *Intermediate IVLE – Subject Home* from the home screen (or, from
the IVLE pulldown menu, choose *Subjects* and select Intermediate IVLE). There
is one worksheet, Worksheet Basics. Clicking this takes you to the worksheet,
where students are challenged by Python questions.

After reading the worksheet, attempt the first simple programming question,
which is to write the "Hello world" program.

First, click *Submit* without writing any code, and note that the system
automatically runs a test case, which fails. Now change the code to be "almost
right" (for example, write ``Hello world`` instead of ``Hello, world!``), and
press *Submit* again. It will tell you that you almost got it right. In this
way, the IVLE test framework can show users that they're on the right track.
If you get it exactly right and click *Submit* a third time, you will pass the
test.

Note that you can also click *Run*, and it will execute your solution in the
Python console. This doesn't cost you an "attempt", nor does it run the test
cases. It just lets you test it out for yourself before making an official
submission.

Back on the subject page, you will notice that the exercise appears complete,
and you have been awarded a mark.

A sample solution to the second exercise follows::

 def fac(n):
     if n == 0:
         return 1
     else:
         return n * fac(n-1)
 
 def main():
     f = int(raw_input())
     print fac(f)

A lecturer's view
=================

Log into IVLE as a lecturer (username: ``lecturer``, password: ``password``).
Many of these things are also possible as a tutor (try username: ``tutor``,
password: ``password``).

Being a lecturer or tutor is a per-subject privilege, so it only applies to
certain subjects. All of your special powers are under the subject home for
the subjects you are a tutor in. Note that everything a lecturer can do, an
admin can also do, for all subjects in the system.

Click *Intermediate IVLE – Subject home* (the one which does not display a
semester -- implying the currently active semester). From here, you will see
largely the same view as a student, but with more buttons. *Change details*
allows you to modify the subject properties. *Administer enrolments* allows
you to add existing IVLE users as students or tutors of the subject you are
teaching, change the roles of existing members, and revoke enrolments.

Managing projects
-----------------

Click *Manage projects* to go to the project management screen. Note that the
3 projects are grouped into "Solo projects" (projects submitted by each
individual student) and "Group projects". Try adding a new Solo project, by
clicking on *Add a new project* within that box. The fields should be fairly
self-explanatory.

Group projects are complicated by what we call "project sets". A "project set"
is a set of group projects where the student groups are the same throughout.
For instance, you will see Phase 2 and Phase 3 inside the same project set
box. This means students will get into groups of 3 to submit Phase 2, and then
the same group will submit Phase 3.

Clicking *Manage groups* lets you put students into groups for a given project
set.

Click *Add a new project set* and enter a group size of 6. Then, create a
project in the new set. Each student must get into a new group for each
project *set*. Note also that the groups will share a Subversion repository
for all projects in a set, but if you create a new set, the students will have
to start using a new repository.

.. warning::
   You can't delete a project set after it has been created (this could cause
   problems for groups and their repositories).

Usually, the hassle of getting into new groups and creating new repositories
means that you will want to create just two project sets for a subject: one
for solo projects, and another for group projects.

Viewing submissions
-------------------

Lecturers and tutors can view any student or group's project submission, using
an external Subversion client. As submissions are really just Subversion
commits, you can examine a student's work by simply checking out the correct
revision of the repository.

From the offering page, click *View submissions* under the project of interest.
This takes you to a page which lists the latest submissions from every student
(presumably you will just see the submission made by ``studenta`` earlier in
this tour). Next to each submission is a command line, beginning with
``svn co``. For instance, you might see the line::

 svn co --username lecturer -r7 http://svn.ivle.localhost/users/studenta/ivle-102/phase1.html

Paste this line into a command-line (or, if you use a GUI Subversion client,
use the username, revision and URL given). Subversion will likely prompt for a
password. For the sample data, this password is ``password``, but in general, it
will **not** be your normal IVLE password. You can learn your Subversion
password by opening a Console in IVLE and typing::

 import ivle.config
 ivle.config.Config()['user_info']['svn_pass']

This will check out the student's work into the current directory, to inspect.

You can also try to check out the group submission from Phase 2.

.. warning::
   It is currently not possible to check out a single file (not a directory)
   submission using the instructions given. Instead, run ``svn cat``, and
   redirect the output into a file.

Managing worksheets and exercises
---------------------------------

Returning to the subject home page, click *Manage worksheets*. On this page,
you will see all of the worksheets for the subject. Here you can edit
worksheets, add new ones, and re-order them. You can also edit any worksheet
from its own page.

To get an idea of what a worksheet looks like in edit mode, click the edit
action (pencil) next to "Worksheet Basics".

* The *URL name* is the name of the worksheet as it appears in URLs.
* The *Assessable* checkbox will make the exercises in the worksheet count
  towards each student's worksheet mark, if checked. Uncheck it for
  informational worksheets.
* The *Format* selection controls the format used to write the worksheet in
  the box below. Leave it on *reStructuredText* unless you have a reason not
  to.

Now, you can edit the worksheet content in reStructuredText. The existing text
briefly explains this format. See `A ReStruecturedText Primer
<http://docutils.sourceforge.net/docs/user/rst/quickstart.html>`_ for a full
guide. Note that the exercises themselves are not defined in the worksheet.
They are separate resources, which can be shared across subjects. Exercises
can be embedded with a line like this::

 .. exercise:: factorial

Click *Manage exercises* to see the exercises (in the sample data, just
``factorial``). An exercise is a very complex thing, due to the fact that it
runs automated testing on the student code. The details are outside the scope
of this tour. Hopefully, you can figure out how they work by examining the
existing ``factorial`` exercise.

If you are game enough, create a new worksheet from scratch. If you are
*really* game, create a new exercise for your worksheet.

Viewing worksheet marks
-----------------------

You will probably have already noticed that the lecturer's worksheet view is
not quite like the student's. It has a table at the top which shows some
statistics about how students in this subject are going with each exercise.
(Depending on settings, tutors may also be able to access these stats.)

Lecturers (not tutors) can also get more specific feedback on individual
students by selecting "View worksheet marks" at the bottom of the subject
page. This shows the marks in each worksheet, and in the subject overall, for
each student, and can be used to calculate each student's final grade.

.. note::
   The marks are calculated from the current time, by default. However,
   normally, there is a cutoff time after which students cannot gain any
   additional marks for worksheets. You can set this cutoff in the offering
   edit page. Once set, the marks will be calculated based on submissions up
   until that date, and students will be notified of the cutoff time.

The "Download as CSV file" link provides these same statistics in CSV format,
which can be easily parsed.

An administrator's view
=======================

Log into IVLE as an admin (username: ``admin``, password: ``password``).

Administrator users in IVLE have significant privileges. Note, however, that
for technical reasons, admins cannot read or write other users' files. This
requires root access on the machine IVLE is installed on.

Administering users
-------------------

Firstly, pull down the IVLE menu (top-left). There is an additional item for
admins -- the *Users* page. This lists all users with an account in IVLE.
Clicking on a username takes you to the user's profile page. Try it with the
user ``lecturer``.

The profile page is exactly the same as the user himself would see it, but
with a few more buttons on the side. *Change password* is the same as the
user's own *Change password* page. However, *Reset password* is a special
admin page which lets you change a user's password without knowing the old
one. *Administer user* also lets you change administrative settings for the
user, such as their full name (more formal than display name, which the user
themselves can change) and student ID. You can also add/remove admin status
for, or disable/enable (i.e., ban from IVLE) any user (except yourself, of
course -- that could be bad).

.. warning::
   Use this with care. Making a user an admin gives them complete control over
   the system. They could even revoke *your* admin rights!

Administering subjects and offerings
------------------------------------

Admin users also enjoy the same privileges as lecturers, for all subject
offerings on the system. In addition, admins can enrol users in an offering as
lecturers (this is the only way to become a lecturer), and change or delete a
lecturer's enrolment. Go to the subject page for Advanced IVLE and enrol the
user ``lecturer`` as a lecturer in the subject.

Admins can also administer subjects. Here it is important to distinguish
between a "subject" (a course on a specific topic which is repeated over a
number of semesters or years) and an "offering" (a particular instance of a
subject, for one semester). Lecturers can administer *offerings* they are
enrolled in, but not *subjects*.

As an admin, go to the *Subjects* page. You will see a link *Manage subjects
and semesters*. The list at the top of the page shows all registered
subjects. Click *Create new subject* to create a brand new subject (i.e., a
new course). Call it "Introduction to Programming", with the URL name
``intro-prog`` and subject code 200101.

Now we have created a *subject* but not an *offering*, so nobody will be able
to teach or enrol in this subject. From the "Introduction to Programming"
page, click *Create new offering*. Select the semester in which the subject
will be first taught. If you wish to create the first offering of a semester
(e.g., 2011 semester 1), you will have to create a new semester first. Type
in a subject description. (Note that each offering has an independent
description.) Once you have created an offering, you can enrol lecturers, and
they can in turn enrol students.

Lecturers can take over administration duties of an offering (such as editing
the description and managing projects), however it remains the admin's duty to
administer the subjects, including creating new offerings each semester and
enrolling lecturers.

Administering semesters
-----------------------

An important duty of the administrator is controlling the *state* of each
semester. Return to the *Manage subjects and semesters* page. Note the
*Semesters* table contains a list of all known semesters, and whether they are
"past", "current" or "future".

.. note::
   IVLE could automatically create and manage semesters based on the system
   clock, but it presently does not. That is because your institution may have
   a different concept of a "semester" to ours. (For example, what are the
   semester start and end dates?) IVLE has therefore been designed to require
   admins to manually activate new semesters and disable old ones.

In the sample data, 2009 semester 2 is the "current" semester. Let us assume
that we are moving into the start of 2010. Edit 2009 semester 2 and set its
state to "Past". Then, edit 2010 semester 1 and set its state to "Current".
This affects the system in several ways. Mainly, it just changes the UI for
all users, in terms of which offerings are presented as "current".

.. warning::
   Marking a semester as anything other than "current" will make it impossible
   for students enrolled in offerings for that semester to submit projects.
   Only do this after the semester has fully closed.

It is possible for multiple semesters to be marked as "current", if this is
desired. Therefore, there is no need to disable one semester before enabling
another.

Admin scripts
-------------

Unfortunately, there are still a few tasks which admins need to do which
haven't been implemented in the UI for the IVLE web application. These tasks
are available as command-line scripts which can be run by someone with root
access on the machine IVLE is installed on. They are gradually being migrated
over to proper UI features in IVLE itself.

Details on these scripts can be found in :ref:`ref-admin-scripts`.
