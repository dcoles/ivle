BEGIN;
DROP TRIGGER deactivate_semester_enrolments ON semester;
DROP FUNCTION deactivate_semester_enrolments_update();
DROP TRIGGER confirm_active_semester ON enrolment;
DROP FUNCTION confirm_active_semester_insertupdate();

ALTER TABLE semester ADD COLUMN state TEXT NOT NULL DEFAULT 'current';
ALTER TABLE semester ADD CONSTRAINT semester_state_check CHECK (state IN ('disabled', 'past', 'current', 'future'));
UPDATE semester SET state='past' WHERE active='false';
ALTER TABLE semester DROP COLUMN active;
COMMIT;
