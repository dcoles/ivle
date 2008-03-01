CREATE TABLE login (
    loginid     SERIAL PRIMARY KEY NOT NULL,
    login       VARCHAR UNIQUE NOT NULL,
    passhash    VARCHAR,
    state	VARCHAR NOT NULL CHECK (state in ('no_agreement', 'pending',
                                              'enabled', 'disabled')),
    rolenm      VARCHAR NOT NULL CHECK (rolenm in ('anyone', 'student',
                                                   'marker', 'tutor',
                                                   'lecturer', 'admin')),
    unixid      INT UNIQUE NOT NULL, -- unix user id
    nick        VARCHAR NOT NULL,
    pass_exp    TIMESTAMP,
    acct_exp    TIMESTAMP,
    last_login  TIMESTAMP,
    svn_pass    VARCHAR,
    email       VARCHAR,
    fullname    VARCHAR NOT NULL,
    studentid   VARCHAR, -- may be null
    settings    VARCHAR
);

CREATE TABLE offering (
    offeringid  SERIAL PRIMARY KEY NOT NULL,
    subj_name   VARCHAR NOT NULL,
    subj_code   VARCHAR NOT NULL,
    year        CHAR(4) NOT NULL,
    semester    CHAR(1) NOT NULL,
    url         VARCHAR
);

CREATE TABLE project (
    projectid   SERIAL PRIMARY KEY NOT NULL,
    synopsis    VARCHAR,
    url         VARCHAR,
    offeringid  INT4 REFERENCES offering (offeringid) NOT NULL,
    deadline    TIMESTAMP
);

CREATE TABLE project_group (
    groupnm     VARCHAR NOT NULL,
    groupid     SERIAL PRIMARY KEY NOT NULL,
    offeringid  INT4 REFERENCES offering (offeringid),
    nick        VARCHAR,
    createdby   INT4 REFERENCES login (loginid) NOT NULL,
    epoch       TIMESTAMP NOT NULL,
    UNIQUE (offeringid, groupnm)
);

CREATE TABLE group_invitation (
    loginid     INT4 REFERENCES login (loginid) NOT NULL,
    groupid     INT4 REFERENCES project_group (groupid) NOT NULL,
    inviter     INT4 REFERENCES login (loginid) NOT NULL,
    invited     TIMESTAMP NOT NULL,
    accepted    TIMESTAMP,
    UNIQUE (loginid,groupid)
);

CREATE TABLE group_member (
    loginid     INT4 REFERENCES login (loginid),
    groupid     INT4 REFERENCES project_group (groupid),
    projectid   INT4 REFERENCES project (projectid),
    UNIQUE (loginid,projectid),
    PRIMARY KEY (loginid,groupid)
);

CREATE TABLE enrolment (
    loginid     INT4 REFERENCES login (loginid),
    offeringid  INT4 REFERENCES offering (offeringid),
    result      INT,
    special_result VARCHAR,
    supp_result INT,
    special_supp_result VARCHAR,
    notes       VARCHAR,
    PRIMARY KEY (loginid,offeringid)
);

CREATE TABLE assessed (
    assessedid  SERIAL PRIMARY KEY NOT NULL,
    loginid     INT4 REFERENCES login (loginid),
    groupid     INT4 REFERENCES project_group (groupid),
    -- exactly one of loginid and groupid must be non-null
    CHECK ((loginid IS NOT NULL AND groupid IS NULL)
        OR (loginid IS NULL AND groupid IS NOT NULL))
);

CREATE TABLE project_extension (
    assessedid  INT4 REFERENCES assessed (assessedid) NOT NULL,
    projectid   INT4 REFERENCES project (projectid) NOT NULL,
    deadline    TIMESTAMP NOT NULL,
    approver    INT4 REFERENCES login (loginid) NOT NULL,
    notes       VARCHAR
);

CREATE TABLE project_mark (
    assessedid  INT4 REFERENCES assessed (assessedid) NOT NULL,
    projectid   INT4 REFERENCES project (projectid) NOT NULL,
    componentid INT4,
    marker      INT4 REFERENCES login (loginid) NOT NULL,
    mark        INT,
    marked      TIMESTAMP,
    feedback    VARCHAR,
    notes       VARCHAR
);

CREATE TABLE problem (
    problemid   SERIAL PRIMARY KEY NOT NULL,
    spec        VARCHAR
);

CREATE TABLE problem_tag (
    problemid   INT4 REFERENCES problem (problemid),
    tag         VARCHAR NOT NULL,
    description VARCHAR,
    standard    BOOLEAN NOT NULL,
    added_by    INT4 REFERENCES login (loginid) NOT NULL,
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
    standard    BOOLEAN NOT NULL,
    added_by    INT4 REFERENCES login (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    PRIMARY KEY (testcaseid,added_by,tag)
);

CREATE TABLE problem_attempt (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    loginid     INT4 REFERENCES login (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    attempt     VARCHAR NOT NULL,
    complete    BOOLEAN NOT NULL,
    PRIMARY KEY (problemid,loginid,date)
);

CREATE INDEX problem_attempt_index ON problem_attempt (problemid, loginid);

CREATE TABLE problem_attempt_breakdown (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    testcaseid  INT4 REFERENCES problem_test_case (testcaseid) NOT NULL,
    loginid     INT4 REFERENCES login (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    result      BOOLEAN
);

CREATE TABLE problem_prerequisite (
    parent      INT4 REFERENCES problem (problemid) NOT NULL,
    child       INT4 REFERENCES problem (problemid) NOT NULL,
    PRIMARY KEY (parent,child)
);

