DO NOT APPLY THIS MIGRATION WITHOUT READING THE FOLLOWING;
-- This migration will delete all problem attempts and saves.
-- The new database schema links attempts and saves to specific worksheets.
-- Worksheets are linked to specific offerings.
-- Problems are no longer referenced by and id number, instead they are
-- referenced by an identifier TEXT field.
-- This means that in order to save your current data, you must link its
-- worksheet to an offering, and link the attempt to a problem identifier.
-- TODO: Write a script to save the problem attempts somehow.

BEGIN;
-- Move the exercises from being stored as flat files, to being stored in
-- The Database
-- Drop Old, Unused tables.
DROP TABLE problem_attempt_breakdown;
DROP TABLE problem_test_case_tag;
DROP TABLE problem_tag;
DROP TABLE problem_test_case;
DROP TABLE problem_prerequisite; 
TRUNCATE worksheet_problem, worksheet;

-- Remove References to problemid
ALTER TABLE problem_attempt DROP CONSTRAINT problem_attempt_problemid_fkey;
ALTER TABLE problem_save DROP CONSTRAINT problem_save_problemid_fkey;
ALTER TABLE worksheet_problem DROP CONSTRAINT worksheet_problem_problemid_fkey;

-- Add fields to problem necessary to store all exercise information in non-xml
ALTER TABLE problem ADD COLUMN name        TEXT;
ALTER TABLE problem ADD COLUMN description TEXT;
ALTER TABLE problem ADD COLUMN partial     TEXT;
ALTER TABLE problem ADD COLUMN solution    TEXT;
ALTER TABLE problem ADD COLUMN include     TEXT;
ALTER TABLE problem ADD COLUMN num_rows    INT4;
-- Drop (now) unused columns spec and problemid
ALTER TABLE problem DROP COLUMN spec;
ALTER TABLE problem DROP COLUMN problemid;

-- Set problems and worksheets to reference exercises by identifier
ALTER TABLE problem_attempt ADD COLUMN worksheetid INT4 REFERENCES worksheet (worksheetid);
ALTER TABLE problem_attempt DROP COLUMN problemid;
ALTER TABLE problem_attempt ADD COLUMN problemid TEXT REFERENCES problem (identifier);

ALTER TABLE problem_save ADD COLUMN worksheetid INT4 REFERENCES worksheet (worksheetid);
ALTER TABLE problem_save DROP COLUMN problemid;
ALTER TABLE problem_save ADD COLUMN problemid TEXT references problem (identifier);

ALTER TABLE worksheet_problem DROP COLUMN problemid;
ALTER TABLE worksheet_problem ADD COLUMN problemid TEXT REFERENCES problem (identifier);

CREATE TABLE test_suite (
    suiteid     SERIAL UNIQUE NOT NULL,
    problemid   TEXT REFERENCES problem (identifier) NOT NULL,
    description text,
    seq_no      INT4,
    PRIMARY KEY (problemid, suiteid)
);

CREATE TABLE test_case (
    testid      SERIAL UNIQUE NOT NULL,
    suiteid     INT4 REFERENCES test_suite (suiteid) NOT NULL,
    passmsg     TEXT,
    failmsg     TEXT,
    init        TEXT,
    code_type   TEXT,
    code        TEXT,
    testtype    TEXT,
    seq_no    INT4,
    PRIMARY KEY (testid, suiteid)
);

-- Link worksheets to offerings
ALTER TABLE worksheet ADD COLUMN offeringid INT4 REFERENCES offering (offeringid) NOT NULL; 
COMMIT;
