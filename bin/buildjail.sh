#!/bin/sh
# IVLE - Informatics Virtual Learning Environment
# Copyright (C) 2007-2008 The University of Melbourne
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

# Module: buildjail.sh
# Author: David Coles
# Date:   02/02/2008

# This is a script to build a minimal Ubuntu chroot jail in JAIL with a set of 
# SYSTEMPACKAGES and STUDENTPACKAGES added. It downloads these packages from an 
# APT mirror located at MIRROR and will use the latest packages from the 
# release version RELEASE and sections SECTION. After installing it will clean 
# the package cache to save space.

# NOTE: This script will remove the JAIL diretcory and anything contained 
# within. Check the path carefully! 

RELEASE=hardy
SECTIONS="main universe"
JAIL=jail
SYSTEMPACKAGES="python2.5 python-cjson python-svn"
STUDENTPACKAGES="python-numpy python-matplotlib python-scipy \
    python-beautifulsoup python-lxml python-imaging \
    python-simpletal python-nltk python-nltk-data" # elementtree-1.3beta

# FIXME: [hack] Override the default mirror to the local AARNET one.  This 
# should really be a local configuration option, but unfortunately setup.py is 
# a bit of a mess and needs a clean up to support this. For the mean time we'll 
# override it here.

if [ -z "$MIRROR" ]; then
    #MIRROR=http://mirror.aarnet.edu.au/pub/ubuntu/archive/
    MIRROR=http://mirror.gamearena.com.au/ubuntu
    #MIRROR=http://archive.ubuntu.com/ubuntu/ # Default Mirror
fi
echo "Using Mirror: $MIRROR"

# Do we have debootstrap? 
if [ -x /usr/sbin/debootstrap ]; then
    DEBOOTSTRAP="/usr/sbin/debootstrap"
fi

if [ -z "$DEBOOTSTRAP" ]; then
    echo "Error: Debootstrap not found. Is it installed?"
    return 1
fi

echo "Building minimal Jail..."
sudo rm -rf --one-file-system $JAIL
sudo $DEBOOTSTRAP --components=`echo $SECTIONS | tr ' ' ','` \
    --include=ubuntu-keyring \
    --variant=minbase $RELEASE $JAIL $MIRROR

echo "Updating package sources..."
sudo tee $JAIL/etc/apt/sources.list > /dev/null <<SOURCES
# APT Mirrors
deb http://apt.qeuni.net/ivle $RELEASE nltk matplotlib
deb $MIRROR $RELEASE main $SECTIONS
deb $MIRROR $RELEASE-security $SECTIONS
deb $MIRROR $RELEASE-updates $SECTIONS"
SOURCES

echo "Adding packages..."
sudo chroot $JAIL /bin/sh -c "apt-get -y update"
sudo chroot $JAIL /bin/sh -c "apt-get -y --allow-unauthenticated install \
    $SYSTEMPACKAGES $STUDENTPACKAGES"
sudo chroot $JAIL /bin/sh -c "apt-get -y upgrade"
sudo chroot $JAIL /bin/sh -c "apt-get -y clean"

