BEGIN;
ALTER TABLE offering ADD COLUMN max_groups_per_student INT4 DEFAULT 1;
ALTER TABLE offering ADD COLUMN max_students_per_group INT4 DEFAULT 4;
COMMIT;
