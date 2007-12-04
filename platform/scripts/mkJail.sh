#!/bin/sh

usr="$1"

mkdir "/home/informatics/jails/$usr"
mkdir "/home/informatics/jails/$usr/home"
mkdir "/home/informatics/jails/$usr/home/$usr"

for f in `cd /home/informatics/config/jail; find . -print`
do
    if [ -d "$f" ]
    then
        mkdir "jails/$usr/$f"
    else
        ln "$f" "jails/$usr/$f"
    fi
done

chown -R "$usr" "jails/$usr"
chgrp -R `id -g "$usr"` "jails/$usr"

