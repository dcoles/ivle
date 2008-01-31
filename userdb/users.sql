CREATE TABLE user (
    login       VARCHAR UNIQUE NOT NULL,
    loginid     SERIAL PRIMARY KEY NOT NULL,
    nick        VARCHAR,
    fullname    VARCHAR,
    studentid   VARCHAR -- may be null
);

CREATE TABLE offering (
    offeringid  SERIAL PRIMARY KEY NOT NULL,
    subj_name   VARCHAR NOT NULL,
    subj_code   VARCHAR NOT NULL,
    year        CHAR(4) NOT NULL,
    semester    INT NOT NULL
);

CREATE TABLE group (
    groupnm       VARCHAR NOT NULL,
    groupid     SERIAL PRIMARY KEY NOT NULL,
    offeringid  INT4 REFERENCES offering (offeringid),
    nick        VARCHAR,
    UNIQUE (offeringid, groupnm)
);

CREATE TABLE group_invitation (
    loginid     INT4 REFERENCES user (loginid),
    groupid     INT4 REFERENCES group (groupid),
    UNIQUE (loginid,groupid)
);

CREATE TABLE group_member (
    loginid     INT4 REFERENCES user (loginid),
    groupid     INT4 REFERENCES group (groupid),
    projectid   INT4 REFERENCES project (projectid),
    UNIQUE (loginid,projectid),
    PRIMARY KEY (loginid,groupid)
);

CREATE TABLE enrolment (
    loginid     INT4 REFERENCES user (loginid),
    offeringid  INT4 REFERENCES offering (offeringid),
    result      INT,
    supp_result INT,
    notes       VARCHAR,
    PRIMARY KEY (loginid,offeringid)
);

CREATE TABLE ivle_role (
    loginid     INT4 PRIMARY KEY REFERENCES user (loginid),
    rolenm      VARCHAR
);

CREATE TABLE project (
    projectid   SERIAL PRIMARY KEY NOT NULL,
    synopsis    VARCHAR,
    url         VARCHAR,
    offeringid  INT4 REFERENCES offering (offeringid) NOT NULL,
    deadline    TIMESTAMP
);

CREATE TABLE project_extension (
    loginid     INT4 REFERENCES user (loginid),
    groupid     INT4 REFERENCES group (groupid),
    projectid   INT4 REFERENCES project (projectid) NOT NULL,
    deadline    TIMESTAMP NOT NULL,
    approver    INT4 REFERENCES user (loginid) NOT NULL,
    notes       VARCHAR,
    -- exactly one of loginid and groupid must be non-null
    CHECK ((loginid IS NOT NULL AND groupid IS NULL)
        OR (loginid IS NULL AND groupid IS NOT NULL))
);

CREATE TABLE project_mark (
    loginid     INT4 REFERENCES user (loginid),
    groupid     INT4 REFERENCES group (groupid),
    projectid   INT4 REFERENCES project (projectid) NOT NULL,
    componentid INT4,
    marker      INT4 REFERENCES user (loginid) NOT NULL,
    mark        INT,
    marked      TIMESTAMP,
    feedback    VARCHAR,
    notes       VARCHAR,
    -- exactly one of loginid and groupid must be non-null
    CHECK ((loginid IS NOT NULL AND groupid IS NULL)
        OR (loginid IS NULL AND groupid IS NOT NULL))
);

CREATE TABLE problem (
    problemid   SERIAL PRIMARY KEY NOT NULL,
    spec        VARCHAR
);

CREATE TABLE problem_tag (
    problemid   INT4 REFERENCES tutorial_problem (problemid),
    tag         VARCHAR NOT NULL,
    added_by    INT4 REFERENCES user (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    PRIMARY KEY (problemid,added_by,tag)
);

CREATE TABLE problem_test_case (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    testcaseid  SERIAL UNIQUE NOT NULL,
    testcase    VARCHAR,
    description VARCHAR,
    visibility  VARCHAR CHECK (visibility in ('public', 'protected', 'private'))
);

CREATE TABLE problem_test_case_tag (
    testcaseid  INT4 REFERENCES problem_test_case (testcaseid) NOT NULL,
    tag         VARCHAR NOT NULL,
    description VARCHAR,
    added_by    INT4 REFERENCES user (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    PRIMARY KEY (testcaseid,added_by,tag)
);

CREATE TABLE problem_attempt (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    loginid     INT4 REFERENCES user (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    attempt     VARCHAR NOT NULL,
    complete    BOOLEAN NOT NULL,
    PRIMARY KEY (problemid,loginid,date)
);

CREATE INDEX problem_attempt_index ON problem_attempt (problemid, loginid);

CREATE TABLE problem_attempt_breakdown (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    testcaseid  INT4 REFERENCES problem_test_case (testcaseid) NOT NULL,
    loginid     INT4 REFERENCES user (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    result      BOOLEAN
);

CREATE TABLE problem_prerequisite (
    parent      INT4 REFERENCES problem (problemid) NOT NULL,
    child       INT4 REFERENCES problem (problemid) NOT NULL,
    PRIMARY KEY (parent,child)
);

