#! /bin/bash

instapress () { xdotool key --delay 0 "$1"; }
instatype () { xdotool type --delay 0 "$1"; }

getclip () { xclip -o -selection clipboard; }
setclip () { echo "$1" | xclip -selection clipboard; }


if [[ "$1" == "secondary" ]]; then
    accents="áéíóú"
else
    accents="àèìòù"
fi
allaccents="àèìòùáéíóú"

oldclip="$(getclip)"
instapress shift+Left
instapress ctrl+c
char="$(getclip)"
char="${char: -1}"
if [[ "$allaccents" == *"$char"* ]]; then
    char="$(echo "$char" | sed "y/$allaccents/aeiouaeiou/")"
else
    char="$(echo "$char" | sed "y/aeiou/$accents/")"
fi
instatype "$char"
setclip "$oldclip"

echo $char
