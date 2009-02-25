BEGIN;
CREATE SEQUENCE login_unixid_seq MINVALUE 1000 MAXVALUE 29999 START WITH 5000;

CREATE TABLE login (
    loginid     SERIAL PRIMARY KEY NOT NULL,
    login       VARCHAR UNIQUE NOT NULL,
    passhash    VARCHAR,
    state	VARCHAR NOT NULL CHECK (state in ('no_agreement', 'pending',
                                              'enabled', 'disabled'))
                                 DEFAULT 'no_agreement',
    admin       BOOLEAN NOT NULL DEFAULT false;
    unixid      INT UNIQUE DEFAULT nextval('login_unixid_seq') NOT NULL,
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

-- Subjects
-- --------

CREATE TABLE subject (
    subjectid       SERIAL PRIMARY KEY NOT NULL,
    subj_code       VARCHAR UNIQUE NOT NULL,
    subj_name       VARCHAR NOT NULL,
    subj_short_name VARCHAR UNIQUE NOT NULL,
    url             VARCHAR
);

CREATE TABLE semester (
    semesterid  SERIAL PRIMARY KEY NOT NULL,
    year        CHAR(4) NOT NULL,
    semester    CHAR(1) NOT NULL,
    state       TEXT NOT NULL CHECK state IN ('disabled', 'past',
                                    'current', 'future') DEFAULT 'current',
    UNIQUE (year, semester)
);

CREATE TABLE offering (
    offeringid  SERIAL PRIMARY KEY NOT NULL,
    subject     INT4 REFERENCES subject (subjectid) NOT NULL,
    semesterid  INTEGER REFERENCES semester (semesterid) NOT NULL,
    groups_student_permissions  VARCHAR NOT NULL DEFAULT 'none',
    CHECK (groups_student_permissions in ('none', 'invite', 'create')),
    UNIQUE (subject, semesterid)
);

-- Projects and groups
-- -------------------

CREATE TABLE project_set (
    projectsetid  SERIAL PRIMARY KEY NOT NULL,
    offeringid    INTEGER REFERENCES offering (offeringid) NOT NULL,
    max_students_per_group  INTEGER NOT NULL DEFAULT 4
);

CREATE TABLE project (
    projectid   SERIAL PRIMARY KEY NOT NULL,
    synopsis    VARCHAR,
    url         VARCHAR,
    projectsetid  INTEGER REFERENCES project_set (projectsetid) NOT NULL,
    deadline    TIMESTAMP
);

CREATE TABLE project_group (
    groupnm     VARCHAR NOT NULL,
    groupid     SERIAL PRIMARY KEY NOT NULL,
    projectsetid  INTEGER REFERENCES project_set (projectsetid) NOT NULL,
    nick        VARCHAR,
    createdby   INT4 REFERENCES login (loginid) NOT NULL,
    epoch       TIMESTAMP NOT NULL,
    UNIQUE (projectsetid, groupnm)
);

CREATE OR REPLACE FUNCTION check_group_namespacing_insertupdate()
RETURNS trigger AS '
    DECLARE
        oid INTEGER;
    BEGIN
        SELECT offeringid INTO oid FROM project_set WHERE project_set.projectsetid = NEW.projectsetid;
        PERFORM 1 FROM project_group, project_set WHERE project_set.offeringid = oid AND project_group.projectsetid = project_set.projectsetid AND project_group.groupnm = NEW.groupnm;
        IF found THEN
            RAISE EXCEPTION ''a project group named % already exists in offering ID %'', NEW.groupnm, oid;
        END IF;
        RETURN NEW;
    END;
' LANGUAGE 'plpgsql';

CREATE TRIGGER check_group_namespacing
    BEFORE INSERT OR UPDATE ON project_group
    FOR EACH ROW EXECUTE PROCEDURE check_group_namespacing_insertupdate();

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
    PRIMARY KEY (loginid,groupid)
);

CREATE TABLE enrolment (
    loginid     INT4 REFERENCES login (loginid),
    offeringid  INT4 REFERENCES offering (offeringid),
    role        TEXT NOT NULL CHECK (role IN ('student', 'tutor',
                                              'lecturer')) DEFAULT 'student',
    result      INT,
    special_result VARCHAR,
    supp_result INT,
    special_supp_result VARCHAR,
    notes       VARCHAR,
    active      BOOL NOT NULL DEFAULT true,
    PRIMARY KEY (loginid,offeringid)
);

CREATE TABLE assessed (
    assessedid  SERIAL PRIMARY KEY NOT NULL,
    loginid     INT4 REFERENCES login (loginid),
    groupid     INT4 REFERENCES project_group (groupid),
    projectid   INT4 REFERENCES project (projectid) NOT NULL,
    -- exactly one of loginid and groupid must be non-null
    CHECK ((loginid IS NOT NULL AND groupid IS NULL)
        OR (loginid IS NULL AND groupid IS NOT NULL))
);

CREATE TABLE project_extension (
    assessedid  INT4 REFERENCES assessed (assessedid) NOT NULL,
    deadline    TIMESTAMP NOT NULL,
    approver    INT4 REFERENCES login (loginid) NOT NULL,
    notes       VARCHAR
);

CREATE TABLE project_submission (
    assessedid  INT4 REFERENCES assessed (assessedid) NOT NULL,
    path        VARCHAR NOT NULL,
    revision    INT4 NOT NULL
);

CREATE TABLE project_mark (
    assessedid  INT4 REFERENCES assessed (assessedid) NOT NULL,
    componentid INT4,
    marker      INT4 REFERENCES login (loginid) NOT NULL,
    mark        INT,
    marked      TIMESTAMP,
    feedback    VARCHAR,
    notes       VARCHAR
);

-- Worksheets
-- ----------
CREATE TABLE exercise (
    identifier  TEXT PRIMARY KEY,
    name        TEXT,
    description TEXT,
    partial     TEXT,
    solution    TEXT,
    include     TEXT,
    num_rows    INT4
);

CREATE TABLE worksheet (
    worksheetid SERIAL PRIMARY KEY,
    offeringid  INT4 REFERENCES offering (offeringid) NOT NULL,
    identifier  TEXT NOT NULL,
    name        TEXT NOT NULL,
    data        TEXT NOT NULL,
    assessable  BOOLEAN NOT NULL,
    seq_no      INT4 NOT NULL,
    format      TEXT NOT NUll,
    UNIQUE (offeringid, identifier)
);

CREATE TABLE worksheet_exercise (
    ws_ex_id        SERIAL PRIMARY KEY,
    worksheetid     INT4 REFERENCES worksheet (worksheetid) NOT NULL,
    exerciseid      TEXT REFERENCES exercise (identifier) NOT NULL,
    seq_no          INT4 NOT NULL,
    active          BOOLEAN NOT NULL DEFAULT true,
    optional        BOOLEAN NOT NULL,
    UNIQUE (worksheetid, exerciseid)
);

CREATE TABLE exercise_attempt (
    loginid     INT4 REFERENCES login (loginid) NOT NULL,
    ws_ex_id    INT4 REFERENCES worksheet_exercise (ws_ex_id) NOT NULL,
    date        TIMESTAMP NOT NULL,
    attempt     TEXT NOT NULL,
    complete    BOOLEAN NOT NULL,
    active      BOOLEAN NOT NULL DEFAULT true,
    PRIMARY KEY (loginid, ws_ex_id, date)
);

CREATE TABLE exercise_save (
    loginid     INT4 REFERENCES login (loginid) NOT NULL,
    ws_ex_id    INT4 REFERENCES worksheet_exercise (ws_ex_id) NOT NULL,
    date        TIMESTAMP NOT NULL,
    text        TEXT NOT NULL,
    PRIMARY KEY (loginid, ws_ex_id)
);

CREATE TABLE test_suite (
    suiteid     SERIAL PRIMARY KEY,
    exerciseid  TEXT REFERENCES exercise (identifier) NOT NULL,
    description TEXT,
    seq_no      INT4,
    function    TEXT,
    stdin       TEXT
);

CREATE TABLE test_case (
    testid          SERIAL PRIMARY KEY,
    suiteid         INT4 REFERENCES test_suite (suiteid) NOT NULL,
    passmsg         TEXT,
    failmsg         TEXT,
    test_default    TEXT,
    seq_no          INT4
);

CREATE TABLE suite_variable (
    varid       SERIAL PRIMARY KEY,
    suiteid     INT4 REFERENCES test_suite (suiteid) NOT NULL,
    var_name    TEXT,
    var_value   TEXT,
    var_type    TEXT NOT NULL,
    arg_no      INT4
);

CREATE TABLE test_case_part (
    partid          SERIAL PRIMARY KEY,
    testid          INT4 REFERENCES test_case (testid) NOT NULL,
    part_type       TEXT NOT NULL,
    test_type       TEXT,
    data            TEXT,
    filename        TEXT
);
COMMIT;
