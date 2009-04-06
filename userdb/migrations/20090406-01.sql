BEGIN;

ALTER TABLE project ALTER COLUMN synopsis TYPE TEXT;
ALTER TABLE project ALTER COLUMN url TYPE TEXT;
ALTER TABLE project ADD COLUMN short_name TEXT NOT NULL;
ALTER TABLE project ADD COLUMN name TEXT NOT NULL;

CREATE OR REPLACE FUNCTION check_project_namespacing_insertupdate()
RETURNS trigger AS '
    DECLARE
        oid INTEGER;
    BEGIN
        IF TG_OP = ''UPDATE'' THEN
            IF NEW.projectsetid = OLD.projectsetid AND NEW.short_name = OLD.short_name THEN
                RETURN NEW;
            END IF;
        END IF;
        SELECT offeringid INTO oid FROM project_set WHERE project_set.projectsetid = NEW.projectsetid;
        PERFORM 1 FROM project, project_set
        WHERE project_set.offeringid = oid AND
              project.projectsetid = project_set.projectsetid AND
              project.short_name = NEW.short_name;
        IF found THEN
            RAISE EXCEPTION ''a project named % already exists in offering ID %'', NEW.short_name, oid;
        END IF;
        RETURN NEW;
    END;
' LANGUAGE 'plpgsql';

CREATE TRIGGER check_project_namespacing
    BEFORE INSERT OR UPDATE ON project
    FOR EACH ROW EXECUTE PROCEDURE check_project_namespacing_insertupdate();

ALTER TABLE project_extension ADD COLUMN extensionid SERIAL PRIMARY KEY;

ALTER TABLE project_submission ADD COLUMN submissionid SERIAL PRIMARY KEY;
ALTER TABLE project_submission ADD COLUMN date_submitted TIMESTAMP NOT NULL;
ALTER TABLE project_submission ADD COLUMN submitter INT4 REFERENCES login (loginid) NOT NULL;

COMMIT;
