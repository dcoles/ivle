-- We need a users database to do authorization, manage groups, &c
-- Here's a first cut.

DROP TABLE roles;
DROP TABLE enrolment;
DROP TABLE group_members;
DROP TABLE users;
DROP TABLE groups;

CREATE TABLE users (
    login       varchar(80) PRIMARY KEY,    -- login id
    nick        varchar(80),
    fullname    varchar(80),
    studentid   varchar(80) or NULL  ****
);

CREATE TABLE groups (
    groupid     varchar(18) PRIMARY KEY,    -- group name Y^4-S^9-G^3    **** use offering-id + group number (compound key)
    nick        varchar(80),                -- group nickname
    subject     varchar(9),                 -- subject code         **** use "offerings" table from CASMAS
    year        varchar(4)                  -- when
);

CREATE TABLE group_members (
    login       varchar(80) REFERENCES users (login),
    groupid     varchar(18) REFERENCES groups (groupid)
);

CREATE TABLE enrolment (
    login       varchar(80) REFERENCES users (login),
    subject     varchar(9),
    result
    supp_result
    year        varchar(4)
);

CREATE TABLE roles (
    login       varchar(80) REFERENCES users (login),
    role        varchar(8)
);

CREATE TABLE project (
    projectid
    synopsis
    url
    subject
    deadline
);

CREATE TABLE extension (
    login or groupid
    projectid
    deadline
    approver
    comment
);

CREATE TABLE mark (
    login or groupid
    projectid
    componentid
    marker
    mark
    timestamp
    feedback
    comment
    KEY: (login/groupid, projectid, componentid)
);

################

CREATE TABLE problem (
    problemid
    specification
    test (xml)
);

CREATE TABLE problem_tags (
    problemid
    tag
    added_by
    timestamp
);

CREATE TABLE problem_attempt (
    problemid
    login
    datetime
    submission
    complete (boolean)
    KEY: (problemid, login, datetime)
);

CREATE INDEX indexname ON problem_attempt (problemid, login);

CREATE TABLE problem_attempt_breakdown (
    problemid
    testcaseid
    login
    datetime
    result (boolean)    **** doesnt tell academic which concepts students are struggling with
);

CREATE TABLE problem_test_case (
    problemid
    testcaseid
    testcase (sourced from xml)
    description
    visibility
    tags (xref to tag table; break out)
);

# concept, curriculum, difficulty
CREATE TABLE tag (
    tag
    documentation
    added_by
    timestamp
);

# for multipart problems
CREATE TABLE prerequisite_problem (
    parent_problemid
    child_problemid
);



INSERT INTO users (login,nick) values ('conway', 'Tom');
INSERT INTO roles (login,role) values ('conway', 'student');
INSERT INTO users (login,nick) values ('apeel', 'Andrew');
INSERT INTO roles (login,role) values ('apeel', 'student');
INSERT INTO users (login,nick) values ('mgiuca', 'Matt');
INSERT INTO roles (login,role) values ('mgiuca', 'tutor');
INSERT INTO users (login,nick) values ('sb', 'Steven');
INSERT INTO roles (login,role) values ('sb', 'lecturer');
INSERT INTO users (login,nick) values ('mpp', 'Mike');
INSERT INTO roles (login,role) values ('mpp', 'student');
INSERT INTO users (login,nick) values ('ivo', 'Ivo');
INSERT INTO roles (login,role) values ('ivo', 'admin');

INSERT INTO groups (groupid, nick, subject, year) values ('2007-INFO10001-321', 'Purple Alert', 'INFO10001', '2008');
INSERT INTO groups (groupid, nick, subject, year) values ('2007-INFO10001-322', 'Blind Illuminati', 'INFO10001', '2008');

INSERT INTO group_members (login,groupid) values ('conway', '2007-INFO10001-321');
INSERT INTO group_members (login,groupid) values ('apeel', '2007-INFO10001-321');
INSERT INTO group_members (login,groupid) values ('mgiuca', '2007-INFO10001-321');
INSERT INTO group_members (login,groupid) values ('sb', '2007-INFO10001-321');
INSERT INTO group_members (login,groupid) values ('mpp', '2007-INFO10001-322');
INSERT INTO group_members (login,groupid) values ('ivo', '2007-INFO10001-322');

INSERT INTO enrolment (login,subject,year) values ('conway' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('apeel' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('mgiuca' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('sb' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('mpp' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('ivo' , 'INFO10001', '2008');
