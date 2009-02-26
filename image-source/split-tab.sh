#!/bin/sh

# Takes the name of a PNG file (such as tab.png).
# Splits into 3 images.

BASE=`basename $1 '.png'`

convert "$1" -crop 4x20+0+0 "$BASE-left.png"
convert "$1" -crop 4x20+4+0 "$BASE-mid.png"
convert "$1" -crop 4x20+61+0 "$BASE-right.png"
