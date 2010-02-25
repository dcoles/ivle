BEGIN;

ALTER TABLE exercise ADD COLUMN description_xhtml_cache TEXT;
ALTER TABLE worksheet ADD COLUMN data_xhtml_cache TEXT;

COMMIT;
