BEGIN;
ALTER TABLE assessed ADD projectid INT4 REFERENCES project (projectid) NOT NULL;
ALTER TABLE project_extension DROP projectid;
ALTER TABLE project_submission DROP projectid;
ALTER TABLE project_mark DROP projectid;
COMMIT;
