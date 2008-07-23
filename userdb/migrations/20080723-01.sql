-- WARNING: This will eat babies. And your offerings, enrolments and groups.

-- This will require plpgsql support in the database. This can be achieved with
-- 'createlang plpgsql ivle'.

-- Here we split semesters out into a separate table, and give them and
-- enrolments an active flag. Triggers are used to ensure that we don't
-- have active enrolments in an inactive semester.
-- We also introduce the concept of project sets, which link groups to
-- projects.


BEGIN;

'Comment this line out to acknowledge the warnings.'

DELETE FROM project;
DELETE FROM group_member;
DELETE FROM group_invitation;
DELETE FROM project_group;
DELETE FROM enrolment;
DELETE FROM offering;

CREATE TABLE semester (
    semesterid  SERIAL PRIMARY KEY NOT NULL,
    year        CHAR(4) NOT NULL,
    semester    CHAR(1) NOT NULL,
    active      BOOL NOT NULL,
    UNIQUE (year, semester)
);

CREATE TABLE project_set (
    projectsetid  SERIAL PRIMARY KEY NOT NULL,
    offeringid    INTEGER REFERENCES offering (offeringid) NOT NULL,
    max_students_per_group  INTEGER NOT NULL DEFAULT 4
);

ALTER TABLE offering DROP COLUMN year;
ALTER TABLE offering DROP COLUMN semester;
ALTER TABLE offering DROP COLUMN max_groups_per_student;
ALTER TABLE offering DROP COLUMN max_students_per_group;
ALTER TABLE offering ADD COLUMN semesterid
    INTEGER REFERENCES semester (semesterid) NOT NULL;
ALTER TABLE offering ADD CONSTRAINT offering_subject_key
    UNIQUE (subject, semesterid);

ALTER TABLE project DROP COLUMN offeringid;
ALTER TABLE project ADD COLUMN projectsetid
    INTEGER REFERENCES project_set (projectsetid) NOT NULL;

ALTER TABLE project_group DROP COLUMN offeringid;
ALTER TABLE project_group ADD COLUMN projectsetid
    INTEGER REFERENCES project_set (projectsetid) NOT NULL;
ALTER TABLE project_group ADD CONSTRAINT project_group_projectsetid_key
    UNIQUE (projectsetid, groupnm);


ALTER TABLE group_member DROP COLUMN projectid;

ALTER TABLE enrolment ADD COLUMN active BOOL NOT NULL DEFAULT true;

-- Triggers

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

CREATE OR REPLACE FUNCTION check_group_namespacing_insertupdate()
RETURNS trigger AS '
    DECLARE
        oid INTEGER;
    BEGIN
        SELECT offeringid INTO oid FROM project_set WHERE project_set.projectsetid = NEW.projectsetid;
        PERFORM 1 FROM project_group, project_set WHERE project_group.projectsetid = project_set.projectsetid AND project_group.groupnm = NEW.groupnm;
        IF found THEN
            RAISE EXCEPTION ''a project group named % already exists in offering ID %'', NEW.groupnm, oid;
        END IF;
        RETURN NEW;
    END;
' LANGUAGE 'plpgsql';

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

CREATE TRIGGER deactivate_semester_enrolments
    AFTER UPDATE ON semester
    FOR EACH ROW EXECUTE PROCEDURE deactivate_semester_enrolments_update();

CREATE TRIGGER check_group_namespacing
    BEFORE INSERT OR UPDATE ON project_group
    FOR EACH ROW EXECUTE PROCEDURE check_group_namespacing_insertupdate();

CREATE TRIGGER confirm_active_semester
    BEFORE INSERT OR UPDATE ON enrolment
    FOR EACH ROW EXECUTE PROCEDURE confirm_active_semester_insertupdate();

COMMIT;
