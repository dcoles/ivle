import os

def setup(uid, jail, cwd):
    if uid == 0:
        raise Exception, 'I will not setup a root jail! Go away!'

    # FIXME - config this
    os.chroot(os.path.join('<<jail_base>>', jail))
    os.chdir(cwd)
    os.setuid(uid)

