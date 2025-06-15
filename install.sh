#!/usr/bin/env bash

packages=$(dunst rofi waybar wlogout grim slurp power-profiles-daemon)

if [[ ! -z $packages ]]; then
    sudo pacman -Sy $packages
fi