DROP TABLE users CASCADE;
CREATE TABLE users (
    login       VARCHAR UNIQUE NOT NULL,
    loginid     SERIAL PRIMARY KEY NOT NULL,
    nick        VARCHAR,
    fullname    VARCHAR,
    studentid   VARCHAR -- may be null
);

DROP TABLE offerings CASCADE;
CREATE TABLE offerings (
    offeringid  SERIAL PRIMARY KEY NOT NULL,
    subj_name   VARCHAR NOT NULL,
    subj_code   VARCHAR NOT NULL,
    year        CHAR(4) NOT NULL,
    semester    INT NOT NULL
);

DROP TABLE groups CASCADE;
CREATE TABLE groups (
    groupnm       VARCHAR NOT NULL,
    groupid     SERIAL PRIMARY KEY NOT NULL,
    offeringid  INT4 REFERENCES offerings (offeringid),
    nick        VARCHAR,
    UNIQUE (offeringid, groupnm)
);

DROP TABLE group_invitations CASCADE;
CREATE TABLE group_invitations (
    loginid     INT4 REFERENCES users (loginid),
    groupid     INT4 REFERENCES groups (groupid),
    UNIQUE (loginid,groupid)
);

DROP TABLE group_members CASCADE;
CREATE TABLE group_members (
    loginid     INT4 REFERENCES users (loginid),
    groupid     INT4 REFERENCES groups (groupid),
    projectid   INT4 REFERENCES projects (projectid),
    UNIQUE (loginid,projectid),
    PRIMARY KEY (loginid,groupid)
);

DROP TABLE enrolment CASCADE;
CREATE TABLE enrolment (
    loginid     INT4 REFERENCES users (loginid),
    offeringid  INT4 REFERENCES offerings (offeringid),
    result      INT,
    supp_result INT,
    notes       VARCHAR,
    PRIMARY KEY (loginid,offeringid)
);

DROP TABLE roles CASCADE;
CREATE TABLE roles (
    loginid     INT4 PRIMARY KEY REFERENCES users (loginid),
    role        VARCHAR
);

DROP TABLE projects CASCADE;
CREATE TABLE projects (
    projectid   SERIAL PRIMARY KEY NOT NULL,
    synopsis    VARCHAR,
    url         VARCHAR,
    offeringid  INT4 REFERENCES offerings (offeringid) NOT NULL,
    deadline    TIMESTAMP
);

DROP TABLE project_extension CASCADE;
CREATE TABLE project_extension (
    loginid     INT4 REFERENCES users (loginid),
    groupid     INT4 REFERENCES groups (groupid),
    projectid   INT4 REFERENCES projects (projectid) NOT NULL,
    deadline    TIMESTAMP NOT NULL,
    approver    INT4 REFERENCES users (loginid) NOT NULL,
    notes       VARCHAR,
    -- exactly one of loginid and groupid must be non-null
    CHECK ((loginid IS NOT NULL AND groupid IS NULL)
        OR (loginid IS NULL AND groupid IS NOT NULL))
);

DROP TABLE project_mark CASCADE;
CREATE TABLE project_mark (
    loginid     INT4 REFERENCES users (loginid),
    groupid     INT4 REFERENCES groups (groupid),
    projectid   INT4 REFERENCES projects (projectid) NOT NULL,
    componentid INT4,
    marker      INT4 REFERENCES users (loginid) NOT NULL,
    mark        INT,
    marked      TIMESTAMP,
    feedback    VARCHAR,
    notes       VARCHAR,
    -- exactly one of loginid and groupid must be non-null
    CHECK ((loginid IS NOT NULL AND groupid IS NULL)
        OR (loginid IS NULL AND groupid IS NOT NULL))
);

DROP TABLE problem CASCADE;
CREATE TABLE problem (
    problemid   SERIAL PRIMARY KEY NOT NULL,
    spec        VARCHAR
);

DROP TABLE problem_tags CASCADE;
CREATE TABLE problem_tags (
    problemid   INT4 REFERENCES tutorial_problem (problemid),
    tag         VARCHAR NOT NULL,
    added_by    INT4 REFERENCES users (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    PRIMARY KEY (problemid,added_by,tag)
);

DROP TABLE problem_test_case CASCADE;
CREATE TABLE problem_test_case (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    testcaseid  SERIAL UNIQUE NOT NULL,
    testcase    VARCHAR,
    description VARCHAR,
    visibility  VARCHAR CHECK (visibility in ('public', 'protected', 'private'))
);

DROP TABLE problem_test_case_tags CASCADE;
CREATE TABLE problem_test_case_tags (
    testcaseid  INT4 REFERENCES problem_test_case (testcaseid) NOT NULL,
    tag         VARCHAR NOT NULL,
    description VARCHAR,
    added_by    INT4 REFERENCES users (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    PRIMARY KEY (testcaseid,added_by,tag)
);

DROP TABLE problem_attempt CASCADE;
CREATE TABLE problem_attempt (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    loginid     INT4 REFERENCES users (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    attempt     VARCHAR NOT NULL,
    complete    BOOLEAN NOT NULL,
    PRIMARY KEY (problemid,loginid,date)
);

DROP INDEX problem_attempt_index;
CREATE INDEX problem_attempt_index ON problem_attempt (problemid, loginid);

DROP TABLE problem_attempt_breakdown CASCADE;
CREATE TABLE problem_attempt_breakdown (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    testcaseid  INT4 REFERENCES problem_test_case (testcaseid) NOT NULL,
    loginid     INT4 REFERENCES users (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    result      BOOLEAN
);

DROP TABLE problem_prerequisites CASCADE;
CREATE TABLE problem_prerequisites (
    parent      INT4 REFERENCES problem (problemid) NOT NULL,
    child       INT4 REFERENCES problem (problemid) NOT NULL,
    PRIMARY KEY (parent,child)
);

