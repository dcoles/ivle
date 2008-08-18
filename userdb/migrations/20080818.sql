-- Adds active column to problem_attempt table
-- This allows a group of problem attempts (ie. from previous semesters) to be
-- marked as 'inactive' and thus counting toward a problem being assessment for
-- the current semester.

ALTER TABLE problem_attempt ADD COLUMN active BOOLEAN NOT NULL DEFAULT true;
