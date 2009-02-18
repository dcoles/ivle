BEGIN;
DO NOT APPLY THIS MIGRATION WITHOUT READING THE FOLLOWING;
-- This migration will delete all problem attempts and saves.
-- The new database schema links attempts and saves to specific worksheets.
-- Worksheets are linked to specific offerings.
-- Problems are no longer referenced by and id number, instead they are
-- referenced by an identifier TEXT field.
-- This means that in order to save your current data, you must link its
-- worksheet to an offering, and link the attempt to a problem identifier.
-- TODO: Write a script to save the problem attempts somehow.

-- Move the exercises from being stored as flat files, to being stored in
-- The Database
-- Drop Old, Unused tables.
DROP TABLE problem_attempt_breakdown;
DROP TABLE problem_test_case_tag;
DROP TABLE problem_tag;
DROP TABLE problem_test_case;
DROP TABLE problem_prerequisite; 
DROP TABLE problem_save;
DROP TABLE problem_attempt;
DROP TABLE worksheet_problem;
DROP TABLE problem;
DROP TABLE worksheet;

CREATE TABLE problem (
    identifier  TEXT PRIMARY KEY,
    name        TEXT,
    description TEXT,
    partial     TEXT,
    solution    TEXT,
    include     TEXT,
    num_rows    INT4
);

CREATE TABLE worksheet (
    worksheetid SERIAL PRIMARY KEY,
    offeringid  INT4 REFERENCES offering (offeringid) NOT NULL,
    identifier  VARCHAR NOT NULL,
    name        TEXT NOT NULL,
    data         TEXT NOT NULL,
    assessable  BOOLEAN,
    order_no    INT4,
    UNIQUE (offeringid, identifier)
);

CREATE TABLE worksheet_problem (
    worksheetid INT4 REFERENCES worksheet (worksheetid) NOT NULL,
    problemid   TEXT REFERENCES problem (identifier) NOT NULL,
    optional    BOOLEAN,
    PRIMARY KEY (worksheetid, problemid)
);

CREATE TABLE problem_attempt (
    problemid   TEXT REFERENCES problem (identifier) NOT NULL,
    loginid     INT4 REFERENCES login (loginid) NOT NULL,
    worksheetid INT4 REFERENCES worksheet (worksheetid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    attempt     VARCHAR NOT NULL,
    complete    BOOLEAN NOT NULL,
    active      BOOLEAN NOT NULL DEFAULT true,
    PRIMARY KEY (problemid,loginid,worksheetid,date)
);

CREATE TABLE problem_save (
    problemid   TEXT REFERENCES problem (identifier) NOT NULL,
    loginid     INT4 REFERENCES login (loginid) NOT NULL,
    worksheetid INT4 REFERENCES worksheet (worksheetid) NOT NULL,
    date        TIMESTAMP NOT NULL,
    text        TEXT NOT NULL,
    PRIMARY KEY (problemid,loginid, worksheetid)
);

CREATE TABLE test_suite (
    suiteid     SERIAL PRIMARY KEY,
    problemid   TEXT REFERENCES problem (identifier) NOT NULL,
    description TEXT,
    seq_no      INT4,
    function    TEXT,
    stdin       TEXT
);

CREATE TABLE test_case (
    testid          SERIAL PRIMARY KEY,
    suiteid         INT4 REFERENCES test_suite (suiteid) NOT NULL,
    passmsg         TEXT,
    failmsg         TEXT,
    test_default    TEXT,
    seq_no          INT4
);

CREATE TABLE suite_variables (
    varid       SERIAL PRIMARY KEY,
    suiteid     INT4 REFERENCES test_suite (suiteid) NOT NULL,
    var_name    TEXT,
    var_value   TEXT,
    var_type    TEXT NOT NULL,
    arg_no      INT4
);

CREATE TABLE test_case_parts (
    partid          SERIAL PRIMARY KEY,
    testid          INT4 REFERENCES test_case (testid) NOT NULL,
    part_type       TEXT NOT NULL,
    test_type       TEXT,
    data            TEXT,
    filename        TEXT
);

COMMIT;
