BEGIN;
ALTER TABLE subject ADD UNIQUE (subj_short_name);
ALTER TABLE subject ALTER COLUMN subj_short_name SET NOT NULL;
COMMIT;
