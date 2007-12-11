-- We need a users database to do authorization, manage groups, &c
-- Here's a first cut.

DROP TABLE roles;
DROP TABLE enrolment;
DROP TABLE group_members;
DROP TABLE users;
DROP TABLE groups;

CREATE TABLE users (
    login       varchar(80) PRIMARY KEY,    -- login id
    nick        varchar(80)
);

CREATE TABLE groups (
    groupid     varchar(18) PRIMARY KEY,    -- group name Y^4-S^9-G^3
    nick        varchar(80),                -- group nickname
    subject     varchar(9),                 -- subject code
    year        varchar(4)                  -- when
);

CREATE TABLE group_members (
    login       varchar(80) REFERENCES users (login),
    groupid     varchar(18) REFERENCES groups (groupid)
);

CREATE TABLE enrolment (
    login       varchar(80) REFERENCES users (login),
    subject     varchar(9),
    year        varchar(4)
);

CREATE TABLE roles (
    login       varchar(80) REFERENCES users (login),
    role        varchar(8)
);

INSERT INTO users (login,nick) values ('conway', 'Tom');
INSERT INTO roles (login,role) values ('conway', 'student');
INSERT INTO users (login,nick) values ('apeel', 'Andrew');
INSERT INTO roles (login,role) values ('apeel', 'student');
INSERT INTO users (login,nick) values ('mgiuca', 'Matt');
INSERT INTO roles (login,role) values ('mgiuca', 'tutor');
INSERT INTO users (login,nick) values ('sb', 'Steven');
INSERT INTO roles (login,role) values ('sb', 'lecturer');
INSERT INTO users (login,nick) values ('mpp', 'Mike');
INSERT INTO roles (login,role) values ('mpp', 'student');
INSERT INTO users (login,nick) values ('ivo', 'Ivo');
INSERT INTO roles (login,role) values ('ivo', 'admin');

INSERT INTO groups (groupid, nick, subject, year) values ('2007-INFO10001-321', 'Purple Alert', 'INFO10001', '2008');
INSERT INTO groups (groupid, nick, subject, year) values ('2007-INFO10001-322', 'Blind Illuminati', 'INFO10001', '2008');

INSERT INTO group_members (login,groupid) values ('conway', '2007-INFO10001-321');
INSERT INTO group_members (login,groupid) values ('apeel', '2007-INFO10001-321');
INSERT INTO group_members (login,groupid) values ('mgiuca', '2007-INFO10001-321');
INSERT INTO group_members (login,groupid) values ('sb', '2007-INFO10001-321');
INSERT INTO group_members (login,groupid) values ('mpp', '2007-INFO10001-322');
INSERT INTO group_members (login,groupid) values ('ivo', '2007-INFO10001-322');

INSERT INTO enrolment (login,subject,year) values ('conway' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('apeel' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('mgiuca' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('sb' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('mpp' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('ivo' , 'INFO10001', '2008');
