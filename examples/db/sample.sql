--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

--
-- Name: assessed_assessedid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('assessed_assessedid_seq', 1, false);


--
-- Name: login_unixid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('login_unixid_seq', 5004, true);


--
-- Name: login_loginid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('login_loginid_seq', 5, true);


--
-- Name: offering_offeringid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('offering_offeringid_seq', 6, true);


--
-- Name: project_extension_extensionid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('project_extension_extensionid_seq', 1, false);


--
-- Name: project_group_groupid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('project_group_groupid_seq', 1, true);


--
-- Name: project_projectid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('project_projectid_seq', 3, true);


--
-- Name: project_set_projectsetid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('project_set_projectsetid_seq', 2, true);


--
-- Name: project_submission_submissionid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('project_submission_submissionid_seq', 1, false);


--
-- Name: semester_semesterid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('semester_semesterid_seq', 4, true);


--
-- Name: subject_subjectid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('subject_subjectid_seq', 4, true);


--
-- Name: suite_variable_varid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('suite_variable_varid_seq', 2, true);


--
-- Name: test_case_part_partid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('test_case_part_partid_seq', 6, true);


--
-- Name: test_case_testid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('test_case_testid_seq', 6, true);


--
-- Name: test_suite_suiteid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('test_suite_suiteid_seq', 3, true);


--
-- Name: worksheet_exercise_ws_ex_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('worksheet_exercise_ws_ex_id_seq', 1, false);


--
-- Name: worksheet_worksheetid_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('worksheet_worksheetid_seq', 1, false);


--
-- Data for Name: assessed; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE assessed DISABLE TRIGGER ALL;



ALTER TABLE assessed ENABLE TRIGGER ALL;

--
-- Data for Name: enrolment; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE enrolment DISABLE TRIGGER ALL;

INSERT INTO enrolment (loginid, offeringid, role, result, special_result, supp_result, special_supp_result, notes, active) VALUES (2, 1, 'lecturer', NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO enrolment (loginid, offeringid, role, result, special_result, supp_result, special_supp_result, notes, active) VALUES (2, 2, 'lecturer', NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO enrolment (loginid, offeringid, role, result, special_result, supp_result, special_supp_result, notes, active) VALUES (3, 2, 'tutor', NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO enrolment (loginid, offeringid, role, result, special_result, supp_result, special_supp_result, notes, active) VALUES (4, 1, 'student', NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO enrolment (loginid, offeringid, role, result, special_result, supp_result, special_supp_result, notes, active) VALUES (4, 2, 'student', NULL, NULL, NULL, NULL, NULL, true);
INSERT INTO enrolment (loginid, offeringid, role, result, special_result, supp_result, special_supp_result, notes, active) VALUES (5, 2, 'student', NULL, NULL, NULL, NULL, NULL, true);


ALTER TABLE enrolment ENABLE TRIGGER ALL;

--
-- Data for Name: exercise; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE exercise DISABLE TRIGGER ALL;

INSERT INTO exercise (identifier, name, description, partial, solution, include, num_rows) VALUES ('factorial', 'Factorial', 'Write a function, `fac`, to compute the **factorial** of a number. e.g.::

    >>> fac(4)
    24

Then, write a function `main`, which reads a number from stdin, and writes its factorial to stdout. e.g.::

    >>> main()
    4
    24
', 'def fac(n):
    pass

def main():
    pass
', 'def fac(n):
    if n == 0:
        return 1
    else:
        return n * fac(n-1)

def main():
    f = int(raw_input())
    print fac(f)', '', 12);


ALTER TABLE exercise ENABLE TRIGGER ALL;

--
-- Data for Name: exercise_attempt; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE exercise_attempt DISABLE TRIGGER ALL;



ALTER TABLE exercise_attempt ENABLE TRIGGER ALL;

--
-- Data for Name: exercise_save; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE exercise_save DISABLE TRIGGER ALL;



ALTER TABLE exercise_save ENABLE TRIGGER ALL;

--
-- Data for Name: group_invitation; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE group_invitation DISABLE TRIGGER ALL;



ALTER TABLE group_invitation ENABLE TRIGGER ALL;

--
-- Data for Name: group_member; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE group_member DISABLE TRIGGER ALL;

INSERT INTO group_member (loginid, groupid) VALUES (4, 1);
INSERT INTO group_member (loginid, groupid) VALUES (5, 1);


ALTER TABLE group_member ENABLE TRIGGER ALL;

--
-- Data for Name: login; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE login DISABLE TRIGGER ALL;

INSERT INTO login (loginid, login, passhash, state, admin, unixid, nick, pass_exp, acct_exp, last_login, svn_pass, email, fullname, studentid, settings) VALUES (1, 'admin', '5f4dcc3b5aa765d61d8327deb882cf99', 'enabled', true, 5000, 'Anne Admin', NULL, NULL, '2009-12-08 11:44:02.285862', 'password', NULL, 'Anne Admin', NULL, NULL);
INSERT INTO login (loginid, login, passhash, state, admin, unixid, nick, pass_exp, acct_exp, last_login, svn_pass, email, fullname, studentid, settings) VALUES (2, 'lecturer', '5f4dcc3b5aa765d61d8327deb882cf99', 'enabled', false, 5001, 'Larry Lecturer', NULL, NULL, '2009-12-08 12:12:16.375628', 'password', NULL, 'Larry Lecturer', NULL, NULL);
INSERT INTO login (loginid, login, passhash, state, admin, unixid, nick, pass_exp, acct_exp, last_login, svn_pass, email, fullname, studentid, settings) VALUES (3, 'tutor', '5f4dcc3b5aa765d61d8327deb882cf99', 'enabled', false, 5002, 'Terry Tutor', NULL, NULL, '2009-12-08 19:08:59.817505', 'password', NULL, 'Terry Tutor', NULL, NULL);
INSERT INTO login (loginid, login, passhash, state, admin, unixid, nick, pass_exp, acct_exp, last_login, svn_pass, email, fullname, studentid, settings) VALUES (4, 'studenta', '5f4dcc3b5aa765d61d8327deb882cf99', 'enabled', false, 5003, 'Alice Student', NULL, NULL, '2009-12-08 12:11:46.349133', 'password', NULL, 'Alice Student', NULL, NULL);
INSERT INTO login (loginid, login, passhash, state, admin, unixid, nick, pass_exp, acct_exp, last_login, svn_pass, email, fullname, studentid, settings) VALUES (5, 'studentb', '5f4dcc3b5aa765d61d8327deb882cf99', 'no_agreement', false, 5004, 'Bob Student', NULL, NULL, NULL, NULL, NULL, 'Bob Student', NULL, NULL);


ALTER TABLE login ENABLE TRIGGER ALL;

--
-- Data for Name: offering; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE offering DISABLE TRIGGER ALL;

INSERT INTO offering (offeringid, subject, semesterid, groups_student_permissions, description, url) VALUES (1, 1, 1, 'none', NULL, 'http://www.ivle.org/example/101');
INSERT INTO offering (offeringid, subject, semesterid, groups_student_permissions, description, url) VALUES (2, 2, 2, 'none', NULL, 'http://www.ivle.org/example/102');
INSERT INTO offering (offeringid, subject, semesterid, groups_student_permissions, description, url) VALUES (3, 1, 3, 'none', NULL, 'http://www.ivle.org/example/101');
INSERT INTO offering (offeringid, subject, semesterid, groups_student_permissions, description, url) VALUES (4, 3, 3, 'none', NULL, 'http://www.ivle.org/example/201');
INSERT INTO offering (offeringid, subject, semesterid, groups_student_permissions, description, url) VALUES (5, 2, 4, 'none', NULL, 'http://www.ivle.org/example/102');
INSERT INTO offering (offeringid, subject, semesterid, groups_student_permissions, description, url) VALUES (6, 4, 4, 'none', NULL, 'http://www.ivle.org/example/202');


ALTER TABLE offering ENABLE TRIGGER ALL;

--
-- Data for Name: project; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE project DISABLE TRIGGER ALL;

INSERT INTO project (projectid, short_name, name, synopsis, url, projectsetid, deadline) VALUES (1, 'phase1', 'Phase 1', 'This is the first project in Intermediate IVLE.', NULL, 1, '2009-08-21 18:00:00');
INSERT INTO project (projectid, short_name, name, synopsis, url, projectsetid, deadline) VALUES (2, 'phase2', 'Phase 2', 'This is the second project in Intermediate IVLE.
Get into groups of 3.', NULL, 2, '2009-09-11 18:00:00');
INSERT INTO project (projectid, short_name, name, synopsis, url, projectsetid, deadline) VALUES (3, 'phase3', 'Phase 3', 'This is the final project in Intermediate IVLE.
Complete this with the same group as Phase 2.', NULL, 2, '2009-09-25 18:00:00');


ALTER TABLE project ENABLE TRIGGER ALL;

--
-- Data for Name: project_extension; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE project_extension DISABLE TRIGGER ALL;



ALTER TABLE project_extension ENABLE TRIGGER ALL;

--
-- Data for Name: project_group; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE project_group DISABLE TRIGGER ALL;

INSERT INTO project_group (groupnm, groupid, projectsetid, nick, createdby, epoch) VALUES ('group1', 1, 2, 'group1', 2, '2009-12-08 17:04:42.981005');


ALTER TABLE project_group ENABLE TRIGGER ALL;

--
-- Data for Name: project_mark; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE project_mark DISABLE TRIGGER ALL;



ALTER TABLE project_mark ENABLE TRIGGER ALL;

--
-- Data for Name: project_set; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE project_set DISABLE TRIGGER ALL;

INSERT INTO project_set (projectsetid, offeringid, max_students_per_group) VALUES (1, 2, NULL);
INSERT INTO project_set (projectsetid, offeringid, max_students_per_group) VALUES (2, 2, 3);


ALTER TABLE project_set ENABLE TRIGGER ALL;

--
-- Data for Name: project_submission; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE project_submission DISABLE TRIGGER ALL;



ALTER TABLE project_submission ENABLE TRIGGER ALL;

--
-- Data for Name: semester; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE semester DISABLE TRIGGER ALL;

INSERT INTO semester (semesterid, year, semester, state) VALUES (1, '2009', '1', 'past');
INSERT INTO semester (semesterid, year, semester, state) VALUES (2, '2009', '2', 'current');
INSERT INTO semester (semesterid, year, semester, state) VALUES (3, '2010', '1', 'future');
INSERT INTO semester (semesterid, year, semester, state) VALUES (4, '2010', '2', 'future');


ALTER TABLE semester ENABLE TRIGGER ALL;

--
-- Data for Name: subject; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE subject DISABLE TRIGGER ALL;

INSERT INTO subject (subjectid, subj_code, subj_name, subj_short_name) VALUES (1, '100101', 'Introduction to IVLE', 'ivle-101');
INSERT INTO subject (subjectid, subj_code, subj_name, subj_short_name) VALUES (2, '100102', 'Intermediate IVLE', 'ivle-102');
INSERT INTO subject (subjectid, subj_code, subj_name, subj_short_name) VALUES (3, '100201', 'Advanced IVLE', 'ivle-201');
INSERT INTO subject (subjectid, subj_code, subj_name, subj_short_name) VALUES (4, '100202', 'Mastering IVLE', 'ivle-202');


ALTER TABLE subject ENABLE TRIGGER ALL;

--
-- Data for Name: suite_variable; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE suite_variable DISABLE TRIGGER ALL;

INSERT INTO suite_variable (varid, suiteid, var_name, var_value, var_type, arg_no) VALUES (1, 1, '', '4', 'arg', 0);
INSERT INTO suite_variable (varid, suiteid, var_name, var_value, var_type, arg_no) VALUES (2, 2, '', '5', 'arg', 0);


ALTER TABLE suite_variable ENABLE TRIGGER ALL;

--
-- Data for Name: test_case; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE test_case DISABLE TRIGGER ALL;

INSERT INTO test_case (testid, suiteid, passmsg, failmsg, test_default, seq_no) VALUES (1, 1, 'Calculates factorial correctly', 'Wrong answer', 'ignore', 0);
INSERT INTO test_case (testid, suiteid, passmsg, failmsg, test_default, seq_no) VALUES (2, 1, 'Doesn''t use functools', 'You used functools, you arrogant git', 'ignore', 1);
INSERT INTO test_case (testid, suiteid, passmsg, failmsg, test_default, seq_no) VALUES (3, 2, 'Calculates factorial correctly', 'Wrong answer', 'ignore', 0);
INSERT INTO test_case (testid, suiteid, passmsg, failmsg, test_default, seq_no) VALUES (5, 3, 'Main worked correctly', 'Main printed something else as well. You should only print out the answer.', 'ignore', 1);
INSERT INTO test_case (testid, suiteid, passmsg, failmsg, test_default, seq_no) VALUES (4, 3, 'Main printout included the correct answer', 'Main didn''t print out the correct answer', 'ignore', 0);
INSERT INTO test_case (testid, suiteid, passmsg, failmsg, test_default, seq_no) VALUES (6, 1, 'Doesn''t use __import__', 'You used __import__, you subversive git!', 'ignore', 2);


ALTER TABLE test_case ENABLE TRIGGER ALL;

--
-- Data for Name: test_case_part; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE test_case_part DISABLE TRIGGER ALL;

INSERT INTO test_case_part (partid, testid, part_type, test_type, data, filename) VALUES (1, 1, 'result', 'match', '', NULL);
INSERT INTO test_case_part (partid, testid, part_type, test_type, data, filename) VALUES (2, 2, 'code', 'check', 'lambda solution, attempt: ''functools'' not in attempt', NULL);
INSERT INTO test_case_part (partid, testid, part_type, test_type, data, filename) VALUES (3, 3, 'result', 'match', '', NULL);
INSERT INTO test_case_part (partid, testid, part_type, test_type, data, filename) VALUES (5, 5, 'stdout', 'norm', 'lambda x: x.strip() # Allow leading or trailing whitespace', NULL);
INSERT INTO test_case_part (partid, testid, part_type, test_type, data, filename) VALUES (4, 4, 'stdout', 'check', 'lambda solution, attempt: solution.strip() in attempt   # Substring test', NULL);
INSERT INTO test_case_part (partid, testid, part_type, test_type, data, filename) VALUES (6, 6, 'code', 'check', 'lambda solution, attempt: ''__import__'' not in attempt', NULL);


ALTER TABLE test_case_part ENABLE TRIGGER ALL;

--
-- Data for Name: test_suite; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE test_suite DISABLE TRIGGER ALL;

INSERT INTO test_suite (suiteid, exerciseid, description, seq_no, function, stdin) VALUES (2, 'factorial', 'Test fac(5)', 1, 'fac', '');
INSERT INTO test_suite (suiteid, exerciseid, description, seq_no, function, stdin) VALUES (1, 'factorial', 'Test fac(4)', 0, 'fac', '');
INSERT INTO test_suite (suiteid, exerciseid, description, seq_no, function, stdin) VALUES (3, 'factorial', 'Test main', 2, 'main', '4
');


ALTER TABLE test_suite ENABLE TRIGGER ALL;

--
-- Data for Name: worksheet; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE worksheet DISABLE TRIGGER ALL;



ALTER TABLE worksheet ENABLE TRIGGER ALL;

--
-- Data for Name: worksheet_exercise; Type: TABLE DATA; Schema: public; Owner: -
--

ALTER TABLE worksheet_exercise DISABLE TRIGGER ALL;



ALTER TABLE worksheet_exercise ENABLE TRIGGER ALL;

--
-- PostgreSQL database dump complete
--

