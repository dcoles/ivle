BEGIN;

-- Check that the provided name is sane for use in URLs.
CREATE OR REPLACE FUNCTION valid_url_name(name text) RETURNS boolean AS 
$$
    BEGIN
        RETURN name ~ E'^[a-z0-9][a-z0-9\+\.\-]*$';
    END;
$$ LANGUAGE 'plpgsql';

-- Just like valid_url_name, except that @ is permitted (so we can use a
-- reasonable subset of email addresses as usernames).
CREATE OR REPLACE FUNCTION valid_login_name(name text) RETURNS boolean AS 
$$
    BEGIN
        RETURN name ~ E'^[a-z0-9][a-z0-9\+\.\-\@]*$';
    END;
$$ LANGUAGE 'plpgsql';

ALTER TABLE login ADD CONSTRAINT login_login_check CHECK (valid_login_name(login)); 
ALTER TABLE subject ADD CONSTRAINT subject_subj_short_name_check CHECK (valid_url_name(subj_short_name)); 
ALTER TABLE semester ADD CONSTRAINT semester_year_check CHECK (valid_url_name(year)); 
ALTER TABLE semester ADD CONSTRAINT semester_semester_check CHECK (valid_url_name(semester)); 
ALTER TABLE project ADD CONSTRAINT project_short_name_check CHECK (valid_url_name(short_name)); 
ALTER TABLE project_group ADD CONSTRAINT project_group_groupnm_check CHECK (valid_url_name(groupnm)); 
ALTER TABLE exercise ADD CONSTRAINT exercise_identifier_check CHECK (valid_url_name(identifier)); 
ALTER TABLE worksheet ADD CONSTRAINT worksheet_identifier_check CHECK (valid_url_name(identifier)); 

COMMIT;
