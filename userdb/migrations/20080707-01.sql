BEGIN;

CREATE TABLE subject (                                                               
    subjectid       SERIAL PRIMARY KEY NOT NULL,
    subj_code       VARCHAR UNIQUE NOT NULL,
    subj_name       VARCHAR NOT NULL,
    subj_short_name VARCHAR,    -- may be null
    url             VARCHAR
);
  
DELETE FROM offering;
ALTER TABLE offering DROP COLUMN subj_code;
ALTER TABLE offering DROP COLUMN subj_name;
ALTER TABLE offering DROP COLUMN url;
ALTER TABLE offering ADD COLUMN subject INT4 REFERENCES subject (subjectid) NOT NULL;

COMMIT;

