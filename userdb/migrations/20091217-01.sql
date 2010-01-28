BEGIN;

ALTER TABLE offering ADD COLUMN description TEXT;
ALTER TABLE offering ADD COLUMN url TEXT;

UPDATE offering SET url = (SELECT url FROM subject WHERE subject.subjectid = offering.subject);

ALTER TABLE subject DROP COLUMN url;

COMMIT;
