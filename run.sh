#!/bin/bash

# Thanks to i3wm's sensible-terminal script
for terminal in "$TERMINAL" x-terminal-emulator mate-terminal gnome-terminal terminator xfce4-terminal urxvt rxvt termit Eterm aterm uxterm xterm roxterm termite lxterminal terminology st qterminal lilyterm tilix terminix konsole kitty guake tilda alacritty hyper wezterm rio; do
    if command -v "$terminal" > /dev/null 2>&1; then
        nohup python $(dirname $0)/netMap.py $terminal >/dev/null 2>&1 &
        exit 0
    fi
done

nohup python $(dirname $0)/netMap.py &
