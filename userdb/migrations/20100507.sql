BEGIN;

-- Add forgotten Assessed uniqueness constraints.
CREATE UNIQUE INDEX assessed_loginid_key ON assessed(loginid, projectid) WHERE loginid IS NOT NULL;
CREATE UNIQUE INDEX assessed_groupid_key ON assessed(groupid, projectid) WHERE groupid IS NOT NULL;

COMMIT;

