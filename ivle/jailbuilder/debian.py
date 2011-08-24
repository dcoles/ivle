# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2009 The University of Melbourne
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

'''Debian-specific bits of the jail building process.'''

import os
import subprocess

from ivle.jailbuilder.exceptions import JailBuildError

def debootstrap_create_jail(release, path, components=['main', 'universe'],
                            mirror=None):
    """Create a Debian-based jail using debootstrap."""
    if mirror is None:
        mirror = 'http://archive.ubuntu.com/ubuntu'
    ec = os.spawnvp(os.P_WAIT, 'debootstrap',
              ['debootstrap', '--components=' + ','.join(components),
               '--include=ubuntu-keyring,gnupg', '--variant=minbase',
               release, path, mirror])
    if ec != 0:
        raise JailBuildError('debootstrap failed with code %d' % ec)

    mangle_sources_list(path, clobber=True)
    mangle_sources_list(path, lines=[
            'deb %s %s%s %s' % (mirror, release, pocket, ' '.join(components))
            for pocket in ('', '-updates', '-security')])

def mangle_sources_list(path, lines=[], clobber=False):
    """Add lines to a sources.list, optionally clobbering an existing one."""
    f = open(os.path.join(path, 'etc/apt/sources.list'),
             'w' if clobber else 'a')

    for line in lines:
        f.write(line + '\n')
    f.close()

def _execute_in_chroot(path, argv, stdin=None):
    """Execute a binary in a chroot, with optional stdin."""
    pid = subprocess.Popen(['chroot', path] + argv, stdin=subprocess.PIPE)
    pid.communicate(stdin)
    if pid.returncode != 0:
        raise JailBuildError('command failed with code %d' % pid.returncode)

def apt_update_cache(path):
    """Update the apt cache in a chroot."""
    _execute_in_chroot(path, ['apt-get', '-y', 'update'])

def apt_upgrade(path):
    """Upgrade apt packages in a chroot."""
    _execute_in_chroot(path, ['apt-get', '-y', 'upgrade'])

def apt_install(path, packages=None):
    """Install apt packages in a chroot."""
    if not packages:
        return
    _execute_in_chroot(path, ['apt-get', '-y', 'install'] + packages)

def apt_clean(path):
    """Clean the apt package cache in a chroot."""
    _execute_in_chroot(path, ['apt-get', 'clean'])

def apt_add_key(path, key_text):
    """Add a key to authenticate apt repositories in a chroot."""
    _execute_in_chroot(path, ['apt-key', 'add', '-'], stdin=key_text)
