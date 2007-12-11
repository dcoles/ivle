import pg

def getCredentials(db, login):
    cred = {}

    res = db.query('SELECT users.nick FROM users WHERE users.login=\'' + login + '\'').dictresult()
    if len(res) <> 1:
        return None
    cred['nick'] = res[0]['nick']

    res = db.query('SELECT groupid FROM group_members WHERE login=\'' + login + '\'').dictresult()
    cred['groups'] = map(lambda x: x.get('groupid'), res)

    res = db.query('SELECT role FROM roles WHERE login=\'' + login + '\'').dictresult()
    if len(res) <> 1:
        return None
    cred['role'] = res[0]['role']

    return cred

def contains(m, l):
    for i in l:
        if m == i:
            return True
    return False

db = pg.connect('tom', 'localhost', 5432, None, None, 'tom', 'sh0r3ham')
c = getCredentials(db, 'conway')

if c['role'] != 'student' or contains('2007-INFO10001-321', c['groups']):
    print c['nick'] + ' may view files for group \'2007-INFO10001-321\'.'

