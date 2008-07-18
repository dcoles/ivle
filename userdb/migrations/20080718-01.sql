BEGIN;
-- Makes unixid a sequence rather than just a int

-- Create a SEQUENCE for unixid 
CREATE SEQUENCE login_unixid_seq MINVALUE 1000 MAXVALUE 29999 START WITH 5000;
ALTER TABLE login ALTER COLUMN unixid SET DEFAULT nextval('login_unixid_seq');
ALTER SEQUENCE login_unixid_seq OWNED BY login.unixid;

-- Set update all the previous unixids to use the sequence
-- Note: This doesn't update the unixid on a users jail files - need to run the update script
UPDATE login SET unixid = nextval('login_unixid_seq');

COMMIT;
