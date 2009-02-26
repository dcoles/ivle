BEGIN;
ALTER TABLE enrolment ADD COLUMN role TEXT NOT NULL CHECK (role IN
                         ('student', 'tutor', 'lecturer')) DEFAULT 'student';
ALTER TABLE login ADD COLUMN admin BOOLEAN NOT NULL DEFAULT false;
UPDATE login SET admin = (rolenm = 'admin');
ALTER TABLE login DROP COLUMN rolenm;
COMMIT;
