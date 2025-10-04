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
  sudo pacman -S --needed --noconfirm git
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
  yay -S --needed --noconfirm "${to_install[@]}"
else
  echo ""
  echo "✅ All packages are already installed!"
fi

# Adding the bash directory files to ~/.bashrc
cat <<EOF >>~/.bashrc
for f in ~/.config/bash/*; do
  . $f
done
EOF

# Post install

# Making directories
mkdir -p "$HOME"/{Desktop,Downloads,Videos,Documents,Music,Pictures}
mkdir -p "$HOME"/Pictures/screenshots
mkdir -p "$HOME"/Videos/screen-recordings
# Cloning wallpapers so that pywal doesn't fail
if [ -d $HOME/Pictures ]; then
  mkdir -p $HOME/Pictures/wallpapers && cd $HOME/Pictures/wallpapers
  git clone https://github.com/ryukamish/wallpapers.git
fi
# Global GNOME theme
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
gsettings set org.gnome.desktop.interface gtk-theme 'Adwaita-dark'

if [ -f "/etc/default/grub" ]; then # Grub
  echo "Detected grub"

  # Backup GRUB config before modifying
  backup_timestamp=$(date +"%Y%m%d%H%M%S")
  sudo cp /etc/default/grub "/etc/default/grub.bak.${backup_timestamp}"

  # Check if splash is already in GRUB_CMDLINE_LINUX_DEFAULT
  if ! grep -q "GRUB_CMDLINE_LINUX_DEFAULT.*splash" /etc/default/grub; then
    # Get current GRUB_CMDLINE_LINUX_DEFAULT value
    current_cmdline=$(grep "^GRUB_CMDLINE_LINUX_DEFAULT=" /etc/default/grub | cut -d'"' -f2)

    # Add splash and quiet if not present
    new_cmdline="$current_cmdline"
    if [[ ! "$current_cmdline" =~ splash ]]; then
      new_cmdline="$new_cmdline splash"
    fi
    if [[ ! "$current_cmdline" =~ quiet ]]; then
      new_cmdline="$new_cmdline quiet"
    fi

    # Trim any leading/trailing spaces
    new_cmdline=$(echo "$new_cmdline" | xargs)

    sudo sed -i "s/^GRUB_CMDLINE_LINUX_DEFAULT=\".*\"/GRUB_CMDLINE_LINUX_DEFAULT=\"$new_cmdline\"/" /etc/default/grub

    # Regenerate grub config
    sudo grub-mkconfig -o /boot/grub/grub.cfg
  else
    echo "GRUB already configured with splash kernel parameters"
  fi
fi

# Add plymouth to HOOKS array after 'base udev' or 'base systemd'
if grep "^HOOKS=" /etc/mkinitcpio.conf | grep -q "base systemd"; then
  sudo sed -i '/^HOOKS=/s/base systemd/base systemd plymouth/' /etc/mkinitcpio.conf
elif grep "^HOOKS=" /etc/mkinitcpio.conf | grep -q "base udev"; then
  sudo sed -i '/^HOOKS=/s/base udev/base udev plymouth/' /etc/mkinitcpio.conf
else
  echo "Couldn't add the Plymouth hook"
fi

# Regenerate initramfs
sudo mkinitcpio -P

# Plymouth theme

if [ -d "/usr/share/plymouth/themes/" ]; then
  sudo cp -r $(pwd)/plymouth/lone /usr/share/plymouth/themes/
else
  sudo mkdir -p /usr/share/plymouth/themes
  sudo cp -r $(pwd)/plymouth/lone /usr/share/plymouth/themes/
fi

if [ -z "sudo plymouth-set-default-theme -l" ]; then
  sudo plymouth-set-default-theme -R lone
else
  echo "❗ Plymouth was not able to set theme!"
fi

# Seamless login after LUKS

if [ ! -f /usr/local/bin/seamless-login ]; then
  sudo cp $(pwd)/scripts/seamless-login /usr/local/bin/seamless-login
else
  echo "✅ Seamless login binary exist!"
fi

if [ ! -f /etc/systemd/system/seamless-login.service ]; then
  cat <<EOF | sudo tee /etc/systemd/system/seamless-login.service
[Unit]
Description=Seamless Auto-Login
Conflicts=getty@tty1.service
After=systemd-user-sessions.service getty@tty1.service plymouth-quit.service systemd-logind.service
PartOf=graphical.target

[Service]
Type=simple
ExecStart=/usr/local/bin/seamless-login uwsm start -- hyprland.desktop
Restart=always
RestartSec=2
StartLimitIntervalSec=30
StartLimitBurst=2
User=$USER
TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes
TTYVTDisallocate=yes
StandardInput=tty
StandardOutput=journal
StandardError=journal+console
PAMName=login

[Install]
WantedBy=graphical.target
EOF
fi

# Systemd units
if [ ! -f /etc/systemd/system/plymouth-quit.service.d/wait-for-graphical.conf ]; then
  # Make plymouth remain until graphical.target
  sudo mkdir -p /etc/systemd/system/plymouth-quit.service.d
  sudo tee /etc/systemd/system/plymouth-quit.service.d/wait-for-graphical.conf <<'EOF'
[Unit]
After=multi-user.target
EOF
fi

# Mask plymouth-quit-wait.service only if not already masked
if ! systemctl is-enabled plymouth-quit-wait.service | grep -q masked; then
  sudo systemctl mask plymouth-quit-wait.service
  sudo systemctl daemon-reload
fi

# Enable seamless-login.service only if not already enabled
if ! systemctl is-enabled seamless-login.service | grep -q enabled; then
  sudo systemctl enable seamless-login.service
fi

# Disable getty@tty1.service only if not already disabled
if ! systemctl is-enabled getty@tty1.service | grep -q disabled; then
  sudo systemctl disable getty@tty1.service
fi

# Wireguard and systemd-resolvconf setup
if ! systemctl is-enabled systemd-resolved.service | grep -q disabled; then
  sudo systemctl enable --now systemd-resolved.service
  sudo systemctl start --now systemd-resolved.service
fi

# Suspend support for laptop
if [ ! -d /etc/systemd/sleep.conf.d ]; then
  sudo mkdir /etc/systemd/sleep.conf.d
else
  sudo tee /etc/systemd/sleep.conf.d/mem-deep.conf <<'EOF'
[Sleep]
MemorySleepMode=deep
EOF
fi
