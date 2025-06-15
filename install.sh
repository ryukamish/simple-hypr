#!/bin/bash

# List of packages to install
packages=("rofi" "grim" "slurp" "waybar" "wlogout" "swappy" "evince")

# Function to check if package is installed
is_installed() {
    if command -v "$1" &> /dev/null || pacman -Qi "$1" &> /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check and install packages
to_install=()
for package in "${packages[@]}"; do
    if is_installed "$package"; then
        echo "✓ $package is already installed"
    else
        echo "✗ $package is not installed"
        to_install+=("$package")
    fi
done

# Install missing packages
if [ ${#to_install[@]} -gt 0 ]; then
    echo ""
    echo "Installing missing packages: ${to_install[*]}"
    sudo pacman -S --needed "${to_install[@]}"
else
    echo ""
    echo "All packages are already installed!"
fi
