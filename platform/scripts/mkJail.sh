#!/bin/sh

usr="$1"
base="/home/informatics"

mkdir "$base/jails/$usr"
mkdir "$base/jails/$usr/home"
mkdir "$base/jails/$usr/home/$usr"

for f in `cd "$base/config/jail"; find . -print`
do
    if [ -d "$base/config/jail/$f" ]
    then
        mkdir "$base/jails/$usr/$f"
    else
        ln "$base/config/jail/$f" "$base/jails/$usr/$f"
    fi
done

chown -R "$usr" "$base/jails/$usr"
chgrp -R `id -g "$usr"` "$base/jails/$usr"

