ALTER TABLE offering ADD COLUMN groups_student_permissions  VARCHAR NOT NULL
    CHECK (groups_student_permissions in ('none', 'invite',
                                          'create'))
    DEFAULT 'none';
