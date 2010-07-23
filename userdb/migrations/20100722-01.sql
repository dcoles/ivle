BEGIN;
ALTER TABLE project_extension DROP deadline;
ALTER TABLE project_extension ADD days INT NOT NULL;
COMMIT;
