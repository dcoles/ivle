CREATE SEQUENCE login_unixid_seq MINVALUE 1000 MAXVALUE 29999 START WITH 5000;

CREATE TABLE login (
    loginid     SERIAL PRIMARY KEY NOT NULL,
    login       VARCHAR UNIQUE NOT NULL,
    passhash    VARCHAR,
    state	VARCHAR NOT NULL CHECK (state in ('no_agreement', 'pending',
                                              'enabled', 'disabled'))
                                 DEFAULT 'no_agreement',
    rolenm      VARCHAR NOT NULL CHECK (rolenm in ('anyone', 'student',
                                                   'marker', 'tutor',
                                                   'lecturer', 'admin')),
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
    active      BOOL NOT NULL,
    UNIQUE (year, semester)
);

CREATE OR REPLACE FUNCTION deactivate_semester_enrolments_update()
RETURNS trigger AS '
    BEGIN
        IF OLD.active = true AND NEW.active = false THEN
            UPDATE enrolment SET active=false WHERE offeringid IN (
            SELECT offeringid FROM offering WHERE offering.semesterid = NEW.semesterid);
        END IF;
        RETURN NULL;
    END;
' LANGUAGE 'plpgsql';

CREATE TRIGGER deactivate_semester_enrolments
    AFTER UPDATE ON semester
    FOR EACH ROW EXECUTE PROCEDURE deactivate_semester_enrolments_update();

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
    result      INT,
    special_result VARCHAR,
    supp_result INT,
    special_supp_result VARCHAR,
    notes       VARCHAR,
    active      BOOL NOT NULL DEFAULT true,
    PRIMARY KEY (loginid,offeringid)
);

CREATE OR REPLACE FUNCTION confirm_active_semester_insertupdate()
RETURNS trigger AS '
    DECLARE
        active BOOL;
    BEGIN
        SELECT semester.active INTO active FROM offering, semester WHERE offeringid=NEW.offeringid AND semester.semesterid = offering.semesterid;
        IF NOT active AND NEW.active = true THEN
            RAISE EXCEPTION ''cannot have active enrolment for % in offering %, as the semester is inactive'', NEW.loginid, NEW.offeringid;
        END IF;
        RETURN NEW;
    END;
' LANGUAGE 'plpgsql';

CREATE TRIGGER confirm_active_semester
    BEFORE INSERT OR UPDATE ON enrolment
    FOR EACH ROW EXECUTE PROCEDURE confirm_active_semester_insertupdate();

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

CREATE TABLE problem (
    problemid   SERIAL PRIMARY KEY NOT NULL,
    identifier  VARCHAR UNIQUE NOT NULL,
    spec        VARCHAR
);

CREATE TABLE worksheet (
    worksheetid SERIAL PRIMARY KEY NOT NULL,
    subject     VARCHAR NOT NULL,
    identifier  VARCHAR NOT NULL,
    assessable  BOOLEAN,
    mtime       TIMESTAMP,
    UNIQUE (subject, identifier)
);

CREATE TABLE worksheet_problem (
    worksheetid INT4 REFERENCES worksheet (worksheetid) NOT NULL,
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    optional    BOOLEAN,
    PRIMARY KEY (worksheetid, problemid)
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
    active      BOOLEAN NOT NULL DEFAULT true,
    PRIMARY KEY (problemid,loginid,date)
);

CREATE TABLE problem_save (
    problemid   INT4 REFERENCES problem (problemid) NOT NULL,
    loginid     INT4 REFERENCES login (loginid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    text        VARCHAR NOT NULL,
    PRIMARY KEY (problemid,loginid)
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

