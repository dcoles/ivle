BEGIN;

ALTER TABLE project ALTER COLUMN deadline SET NOT NULL;

COMMIT;