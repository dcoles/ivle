#!/usr/bin/env python

import os, stat, sys

def update(file, pattern, replacement, verbose=False):
    if verbose:
        print "Updating:", file

    # make sure we can write the file   
    old_perm = os.stat(file)[0]
    if not os.access(file, os.W_OK):
        os.chmod(file, old_perm | stat.S_IWRITE)

    # write the file
    s = open(file, 'rb').read()
    out = open(file, 'wb')
    out.write(s.replace(pattern, replacement))
    out.close()
   
    # restore permissions
    os.chmod(file, old_perm)

            
old_uuid = "4d949360-5a40-0410-921c-d637654a4d6e" # IVLE at SourceForge
new_uuid = "2b9c9e99-6f39-0410-b283-7f802c844ae2" # IVLE at GoogleCode

for root, dirs, files in os.walk('.'):
    if root.endswith('.svn'):
        update(os.path.join(root, 'entries'), old_uuid, new_uuid, True)


