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
    grpnm       varchar(18) PRIMARY KEY,    -- group name Y^4-S^9-G^3
    nick        varchar(80),                -- group nickname
    subject     varchar(9),                 -- subject code
    year        varchar(4)                  -- when
);

CREATE TABLE group_members (
    login       varchar(80) REFERENCES users (login),
    grpnm       varchar(18) REFERENCES groups (grpnm)
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
INSERT INTO users (login,nick) values ('apeel', 'Andrew');
INSERT INTO users (login,nick) values ('mgiuca', 'Matt');
INSERT INTO users (login,nick) values ('sb', 'Steven');
INSERT INTO users (login,nick) values ('mpp', 'Mike');
INSERT INTO users (login,nick) values ('ivo', 'Ivo');

INSERT INTO groups (grpnm, nick, subject, year) values ('2007-INFO10001-321', 'Purple Alert', 'INFO10001', '2008');
INSERT INTO groups (grpnm, nick, subject, year) values ('2007-INFO10001-322', 'Blind Illuminati', 'INFO10001', '2008');

INSERT INTO group_members (login,grpnm) values ('conway', '2007-INFO10001-321');
INSERT INTO group_members (login,grpnm) values ('apeel', '2007-INFO10001-321');
INSERT INTO group_members (login,grpnm) values ('mgiuca', '2007-INFO10001-321');
INSERT INTO group_members (login,grpnm) values ('sb', '2007-INFO10001-321');
INSERT INTO group_members (login,grpnm) values ('mpp', '2007-INFO10001-322');
INSERT INTO group_members (login,grpnm) values ('ivo', '2007-INFO10001-322');

INSERT INTO enrolment (login,subject,year) values ('conway' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('apeel' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('mgiuca' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('sb' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('mpp' , 'INFO10001', '2008');
INSERT INTO enrolment (login,subject,year) values ('ivo' , 'INFO10001', '2008');
