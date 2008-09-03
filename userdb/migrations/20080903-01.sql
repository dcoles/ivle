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
