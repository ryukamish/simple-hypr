#!/bin/bash

# Check for internet connectivity
echo "Checking internet connectivity..."
if ! ping -c 1 google.com &>/dev/null; then
  echo "❌ No internet connection. Exiting."
  exit 1
fi
echo "✓ Internet connection available"

# Check if git is installed
if ! command -v git &>/dev/null; then
  echo "❌ Git is not installed. Installing git..."
  sudo pacman -S --needed git
  if [ $? -ne 0 ]; then
    echo "❌ Failed to install git. Exiting."
    exit 1
  fi
fi
echo "✓ Git is available"

# Check if packages.txt exists
if [ ! -f "packages.txt" ]; then
  echo "❌ packages.txt file not found. Exiting."
  exit 1
fi
echo "✓ packages.txt found"

# Check if yay is installed, if not install it
if ! command -v yay &>/dev/null; then
  echo "Installing yay AUR helper..."
  cd ~/Downloads
  git clone https://aur.archlinux.org/yay-bin.git
  cd yay-bin
  makepkg -si --noconfirm
  cd ..
  rm -rf yay-bin
  cd - >/dev/null

  if ! command -v yay &>/dev/null; then
    echo "❌ Failed to install yay. Exiting."
    exit 1
  fi
fi
echo "✓ yay is available"

# Read packages from packages.txt
packages=()
while IFS= read -r line; do
  [[ -n "$line" ]] && packages+=("$line")
done <packages.txt

# Function to check if package is installed
is_installed() {
  if yay -Qi "$1" &>/dev/null; then
    return 0
  else
    return 1
  fi
}

# Check and install packages
to_install=()
for package in "${packages[@]}"; do
  # Skip empty lines
  if [ -z "$package" ]; then
    continue
  fi

  if is_installed "$package"; then
    echo "✓ $package is already installed"
  else
    echo "✗ $package is not installed"
    to_install+=("$package")
  fi
done

# Install missing packages using yay
if [ ${#to_install[@]} -gt 0 ]; then
  echo ""
  echo "Installing missing packages: ${to_install[*]}"
  yay -S --needed "${to_install[@]}"
else
  echo ""
  echo "✅ All packages are already installed!"
fi

# Adding the bash directory files to ~/.bashrc
cat <<EOF >>~/.bashrc
for file in "$HOME"/.config/bash/*; do
    [[ -f $file ]] && source $file
done
EOF

# Post install
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita-dark'
