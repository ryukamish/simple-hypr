#!/usr/bin/env python3

import os
import sys
import random
import subprocess
import tempfile
from pathlib import Path
from typing import List, Set

class WallpaperManager:
    def __init__(self, wallpaper_dir: str = "~/Pictures/wallpapers"):
        self.wallpaper_dir = Path(wallpaper_dir).expanduser()
        self.used_wallpapers_file = Path(tempfile.gettempdir()) / "wallpaper_manager_used.txt"
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif'}
        
        # Default swww configuration - modify these values as needed
        self.default_swww_config = {
            'transition_type': 'wipe',           # none, simple, fade, left, right, top, bottom, wipe, wave, grow, center, outer, random
            'transition_duration': 2.0,         # Duration in seconds
            'transition_fps': 60,               # Animation FPS
            'transition_angle': 45,             # Angle for wipe transitions (0-359)
            'transition_pos': 'center',         # Position for grow/outer transitions
            'transition_step': 90,              # Step size for wave transitions
            'resize': 'crop',                   # crop, fit, stretch, fill
            'fill_color': '#000000',            # Background fill color in hex
            'filter': 'Lanczos3'                # Nearest, Triangle, CatmullRom, Gaussian, Lanczos3
        }
        
    def get_wallpaper_files(self) -> List[Path]:
        """Get all supported wallpaper files from the wallpaper directory."""
        if not self.wallpaper_dir.exists():
            raise FileNotFoundError(f"Wallpaper directory not found: {self.wallpaper_dir}")
        
        wallpapers = []
        for file_path in self.wallpaper_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_formats:
                wallpapers.append(file_path)
        
        if not wallpapers:
            raise FileNotFoundError(f"No supported wallpaper files found in {self.wallpaper_dir}")
        
        return wallpapers
    
    def get_used_wallpapers(self) -> Set[str]:
        """Get list of wallpapers used in current boot session."""
        if not self.used_wallpapers_file.exists():
            return set()
        
        try:
            with open(self.used_wallpapers_file, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            print(f"Warning: Could not read used wallpapers file: {e}")
            return set()
    
    def mark_wallpaper_as_used(self, wallpaper_path: Path):
        """Mark a wallpaper as used in current boot session."""
        try:
            with open(self.used_wallpapers_file, 'a') as f:
                f.write(f"{wallpaper_path}\n")
        except Exception as e:
            print(f"Warning: Could not update used wallpapers file: {e}")
    
    def get_available_wallpapers(self) -> List[Path]:
        """Get wallpapers that haven't been used in current boot session."""
        all_wallpapers = self.get_wallpaper_files()
        used_wallpapers = self.get_used_wallpapers()
        
        available = [wp for wp in all_wallpapers if str(wp) not in used_wallpapers]
        
        # If all wallpapers have been used, reset and use all wallpapers
        if not available:
            print("All wallpapers have been used. Resetting for this session...")
            self.used_wallpapers_file.unlink(missing_ok=True)
            available = all_wallpapers
        
        return available
    
    def check_dependencies(self):
        """Check if required dependencies are installed."""
        dependencies = ['swww', 'wal']
        missing = []
        
        for dep in dependencies:
            if subprocess.run(['which', dep], capture_output=True).returncode != 0:
                missing.append(dep)
        
        if missing:
            print(f"Error: Missing dependencies: {', '.join(missing)}")
            print("Please install:")
            for dep in missing:
                if dep == 'swww':
                    print("  - swww: https://github.com/Horus645/swww")
                elif dep == 'wal':
                    print("  - pywal: pip install pywal")
            sys.exit(1)
    
    def set_wallpaper_with_swww(self, wallpaper_path: Path, swww_options: dict = None):
        """Set wallpaper using swww with custom options."""
        try:
            # Check if swww daemon is running
            result = subprocess.run(['swww', 'query'], capture_output=True, text=True)
            if result.returncode != 0:
                print("Starting swww daemon...")
                subprocess.run(['swww', 'init'], check=True)
            
            # Use default config if no options provided
            if swww_options is None:
                swww_options = self.default_swww_config
            else:
                # Merge with defaults (command line overrides defaults)
                merged_options = self.default_swww_config.copy()
                merged_options.update(swww_options)
                swww_options = merged_options
            
            # Build swww command with options
            cmd = ['swww', 'img', str(wallpaper_path)]
            
            # Transition type
            if swww_options.get('transition_type'):
                cmd.extend(['--transition-type', swww_options['transition_type']])
            
            # Transition duration
            if swww_options.get('transition_duration'):
                cmd.extend(['--transition-duration', str(swww_options['transition_duration'])])
            
            # Transition FPS
            if swww_options.get('transition_fps'):
                cmd.extend(['--transition-fps', str(swww_options['transition_fps'])])
            
            # Transition angle (for wipe transitions)
            if swww_options.get('transition_angle') is not None:
                cmd.extend(['--transition-angle', str(swww_options['transition_angle'])])
            
            # Transition position (for grow/outer transitions)
            if swww_options.get('transition_pos'):
                cmd.extend(['--transition-pos', swww_options['transition_pos']])
            
            # Transition step (for wave transitions)
            if swww_options.get('transition_step'):
                cmd.extend(['--transition-step', str(swww_options['transition_step'])])
            
            # Resize filter
            if swww_options.get('resize'):
                cmd.extend(['--resize', swww_options['resize']])
            
            # Fill color
            if swww_options.get('fill_color'):
                cmd.extend(['--fill-color', swww_options['fill_color']])
            
            # Filter
            if swww_options.get('filter'):
                cmd.extend(['--filter', swww_options['filter']])
            
            # Set wallpaper
            print(f"Setting wallpaper: {wallpaper_path.name}")
            if swww_options != self.default_swww_config:
                print(f"Using custom swww options: {swww_options}")
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error setting wallpaper with swww: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error with swww: {e}")
            return False
    
    def generate_colorscheme_with_pywal(self, wallpaper_path: Path):
        """Generate color scheme using pywal."""
        try:
            print(f"Generating color scheme from: {wallpaper_path.name}")
            subprocess.run(['wal', '-i', str(wallpaper_path)], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error generating color scheme with pywal: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error with pywal: {e}")
            return False
    
    def change_wallpaper(self, specific_wallpaper: str = None, swww_options: dict = None):
        """Change wallpaper and color scheme."""
        try:
            available_wallpapers = self.get_available_wallpapers()
            
            if specific_wallpaper:
                # Use specific wallpaper if provided
                wallpaper_path = Path(specific_wallpaper).expanduser()
                if not wallpaper_path.exists():
                    # Try to find it in wallpaper directory
                    potential_path = self.wallpaper_dir / specific_wallpaper
                    if potential_path.exists():
                        wallpaper_path = potential_path
                    else:
                        print(f"Error: Wallpaper not found: {specific_wallpaper}")
                        return False
            else:
                # Choose random wallpaper from available ones
                wallpaper_path = random.choice(available_wallpapers)
            
            # Set wallpaper with swww
            if not self.set_wallpaper_with_swww(wallpaper_path, swww_options):
                return False
            
            # Generate color scheme with pywal
            if not self.generate_colorscheme_with_pywal(wallpaper_path):
                return False
            
            # Mark as used
            self.mark_wallpaper_as_used(wallpaper_path)
            
            print(f"Successfully changed wallpaper to: {wallpaper_path.name}")
            return True
            
        except Exception as e:
            print(f"Error changing wallpaper: {e}")
            return False
    
    def list_wallpapers(self):
        """List all available wallpapers."""
        try:
            all_wallpapers = self.get_wallpaper_files()
            used_wallpapers = self.get_used_wallpapers()
            
            print(f"Wallpapers in {self.wallpaper_dir}:")
            print("-" * 50)
            
            for wp in sorted(all_wallpapers):
                status = "[USED]" if str(wp) in used_wallpapers else "[AVAILABLE]"
                print(f"{status} {wp.name}")
                
            print(f"\nTotal: {len(all_wallpapers)} wallpapers")
            print(f"Used in current session: {len(used_wallpapers)}")
            print(f"Available: {len(all_wallpapers) - len(used_wallpapers)}")
            
        except Exception as e:
            print(f"Error listing wallpapers: {e}")
    
    def reset_used_wallpapers(self):
        """Reset the used wallpapers list."""
        try:
            self.used_wallpapers_file.unlink(missing_ok=True)
            print("Reset used wallpapers list.")
        except Exception as e:
            print(f"Error resetting used wallpapers: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Wallpaper manager with swww and pywal")
    parser.add_argument('-d', '--directory', default='~/Pictures/wallpapers',
                       help='Wallpaper directory (default: ~/Pictures/wallpapers)')
    parser.add_argument('-w', '--wallpaper', help='Specific wallpaper to set')
    parser.add_argument('-l', '--list', action='store_true',
                       help='List all wallpapers and their status')
    parser.add_argument('-r', '--reset', action='store_true',
                       help='Reset used wallpapers list')
    
    # swww options (these override the default config in the script)
    parser.add_argument('--transition-type', choices=['none', 'simple', 'fade', 'left', 'right', 'top', 'bottom', 'wipe', 'wave', 'grow', 'center', 'outer', 'random'],
                       help='Transition type (overrides default config)')
    parser.add_argument('--transition-duration', type=float,
                       help='Transition duration in seconds (overrides default config)')
    parser.add_argument('--transition-fps', type=int,
                       help='Transition FPS (overrides default config)')
    parser.add_argument('--transition-angle', type=int, choices=range(0, 360),
                       help='Transition angle for wipe transitions (0-359)')
    parser.add_argument('--transition-pos', type=str,
                       help='Transition position (e.g., "center", "top-left", "0.3,0.8")')
    parser.add_argument('--transition-step', type=int,
                       help='Transition step for wave transitions')
    parser.add_argument('--resize', choices=['crop', 'fit', 'stretch', 'fill'],
                       help='Resize filter (overrides default config)')
    parser.add_argument('--fill-color', type=str,
                       help='Fill color in hex format (e.g., #000000)')
    parser.add_argument('--filter', choices=['Nearest', 'Triangle', 'CatmullRom', 'Gaussian', 'Lanczos3'],
                       help='Image filter (overrides default config)')
    
    args = parser.parse_args()
    
    # Initialize wallpaper manager
    wm = WallpaperManager(args.directory)
    
    # Handle different commands
    if args.list:
        wm.list_wallpapers()
        return
    
    if args.reset:
        wm.reset_used_wallpapers()
        return
    
    # Check dependencies before proceeding
    wm.check_dependencies()
    
    # Build swww options (only include options that were explicitly provided)
    swww_options = {}
    
    if args.transition_type:
        swww_options['transition_type'] = args.transition_type
    if args.transition_duration is not None:
        swww_options['transition_duration'] = args.transition_duration
    if args.transition_fps is not None:
        swww_options['transition_fps'] = args.transition_fps
    if args.transition_angle is not None:
        swww_options['transition_angle'] = args.transition_angle
    if args.transition_pos:
        swww_options['transition_pos'] = args.transition_pos
    if args.transition_step is not None:
        swww_options['transition_step'] = args.transition_step
    if args.resize:
        swww_options['resize'] = args.resize
    if args.fill_color:
        swww_options['fill_color'] = args.fill_color
    if args.filter:
        swww_options['filter'] = args.filter
    
    # Change wallpaper (will use defaults if no options provided)
    if wm.change_wallpaper(args.wallpaper, swww_options if swww_options else None):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
