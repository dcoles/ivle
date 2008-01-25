-- We need a users database to do authorization, manage groups, &c
-- Here's a first cut.

DROP TABLE roles;
DROP TABLE enrolment;
DROP TABLE group_members;
DROP TABLE users;
DROP TABLE groups;

CREATE TABLE users (
    login       VARCHAR UNIQUE NOT NULL,
    loginid     SERIAL PRIMARY KEY NOT NULL,
    nick        VARCHAR,
    fullname    VARCHAR,
    studentid   VARCHAR, -- may be null
);

CREATE TABLE groups (
    group       VARCHAR NOT NULL,
    groupid     SERIAL PRIMARY KEY NOT NULL,
    offeringid  INT4 REFERENCES offerings (offeringid),
    nick        VARCHAR,
    UNIQUE (offeringid, group)
);

CREATE TABLE group_invitations (
    loginid     INT4 REFERENCES users (loginid),
    groupid     INT4 REFERENCES groups (groupid),
    UNIQUE (loginid,groupid)
);

CREATE TABLE group_members (
    loginid     INT4 REFERENCES users (loginid),
    groupid     INT4 REFERENCES groups (groupid),
    projectid   INT4 REFERENCES projects (projectid),
    UNIQUE (loginid,projectid),
    PRIMARY KEY (loginid,groupid)
);

CREATE TABLE enrolment (
    loginid     INT4 REFERENCES users (loginid),
    offeringid  INT4 REFERENCES offerings (offeringid),
    result      INT,
    supp_result INT,
    notes       VARCHAR,
    PRIMARY KEY (loginid,offeringid)
);

CREATE TABLE roles (
    loginid     INT4 PRIMARY KEY REFERENCES users (loginid),
    role        VARCHAR
);

CREATE TABLE projects (
    projectid   SERIAL PRIMARY KEY NOT NULL,
    synopsis    VARCHAR,
    url         VARCHAR,
    offeringid  INT4 REFERENCES offerings (offeringid) NOT NULL,
    deadline    TIMESTAMP
);

CREATE TABLE project_extension (
    login or groupid
    projectid   INT4 REFERENCES projects (projectid) NOT NULL,
    deadline    TIMESTAMP NOT NULL,
    approver    INT4 REFERENCES users (loginid) NOT NULL,
    notes       VARCHAR
);

CREATE TABLE project_mark (
    loginid or groupid
    projectid   INT4 REFERENCES projects (projectid) NOT NULL,
    componentid INT4,
    marker      INT4 REFERENCES users (loginid) NOT NULL,
    mark        INT,
    marked      TIMESTAMP,
    feedback    VARCHAR,
    notes       VARCHAR,
    PRIMARY KEY (loginid/groupid, projectid, componentid)
);

CREATE TABLE problem (
    problemid   SERIAL PRIMARY KEY NOT NULL,
    spec        VARCHAR
);

CREATE TABLE problem_tags (
    problemid   INT4 REFERENCES tutorial_problem (problemid),
    tag         VARCHAR NOT NULL,
    added_by    INT4 REFERENCES users (loginid) NOT NULL,
    when        TIMESTAMP NOT NULL,
    PRIMARY KEY (problemid,added_by,tag)
);

CREATE TABLE problem_test_case (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    testcaseid  SERIAL UNIQUE NOT NULL,
    testcase    VARCHAR,
    description VARCHAR,
    visibility  VARCHAR CHECK (visibility in ('public', 'protected', 'private'))
);

CREATE TABLE problem_test_case_tags (
    testcaseid  INT4 REFERENCES problem_test_case (testcaseid) NOT NULL,
    tag         VARCHAR NOT NULL,
    description VARCHAR,
    added_by    INT4 REFERENCES users (loginid) NOT NULL,
    when        TIMESTAMP NOT NULL,
    PRIMARY KEY (testcaseid,added_by,tag)
);

CREATE TABLE problem_attempt (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    loginid     INT4 REFERENCES users (loginid) NOT NULL,
    when        TIMESTAMP NOT NULL,
    attempt     VARCHAR NOT NULL,
    complete    BOOLEAN NOT NULL,
    PRIMARY KEY (problemid,loginid,when)
);

CREATE INDEX indexname ON problem_attempt (problemid, login);

CREATE TABLE problem_attempt_breakdown (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    testcaseid  INT4 REFERENCES problem_test_case (testcaseid) NOT NULL,
    loginid     INT4 REFERENCES users (loginid) NOT NULL,
    when        TIMESTAMP NOT NULL,
    result      BOOLEAN
);

CREATE TABLE problem_prerequisites (
    parent      INT4 REFERENCES problem (problemid) NOT NULL,
    child       INT4 REFERENCES problem (problemid) NOT NULL,
    PRIMARY KEY (parent,child)
);

