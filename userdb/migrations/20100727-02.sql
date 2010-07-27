BEGIN;

ALTER TABLE semester RENAME COLUMN semester TO url_name;
ALTER TABLE semester ADD COLUMN display_name TEXT;
ALTER TABLE semester ADD COLUMN code TEXT;

UPDATE semester SET code = UPPER(url_name);
UPDATE semester SET display_name = 'semester ' || code;

ALTER TABLE semester ALTER COLUMN display_name SET NOT NULL;
ALTER TABLE semester ALTER COLUMN code SET NOT NULL;

COMMIT;
