#!/usr/bin/env python3
"""
Version update script for XIBE-CHAT CLI
Updates version in ai_cli.py, setup.py, and pyproject.toml
"""

import re
import sys


def update_version_in_file(filepath, pattern, replacement, version):
    """Update version in a file using regex pattern"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the version
        new_content = re.sub(pattern, replacement.format(version=version), content)
        
        # Check if anything was changed
        if content == new_content:
            print(f"Warning: No changes made in {filepath}")
            return False
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ Updated {filepath}")
        return True
    except (FileNotFoundError, PermissionError, IOError) as e:
        print(f"✗ Error updating {filepath}: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <version>")
        print("Example: python update_version.py 0.8.9")
        sys.exit(1)
    
    version = sys.argv[1]
    
    # Validate version format (supports semantic versioning with optional pre-release and build metadata)
    if not re.match(r'^\d+\.\d+\.\d+(-[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?(\+[0-9A-Za-z-]+(\.[0-9A-Za-z-]+)*)?$', version):
        print(f"Error: Invalid version format '{version}'. Expected format: X.Y.Z[-prerelease][+build]")
        print("Examples: 0.8.1, 1.0.0-alpha.1, 1.0.0+build.1, 1.0.0-beta.2+build.123")
        sys.exit(1)
    
    print(f"Updating version to {version}...")
    
    # Define files to update
    files_to_update = [
        ('ai_cli.py', r'CURRENT_VERSION = "[^"]*"', 'CURRENT_VERSION = "{version}"'),
        ('setup.py', r'version="[^"]*"', 'version="{version}"'),
        ('pyproject.toml', r'version = "[^"]*"', 'version = "{version}"'),
    ]
    
    success_count = 0
    total_files = len(files_to_update)
    
    # Update each file
    for filepath, pattern, replacement in files_to_update:
        if update_version_in_file(filepath, pattern, replacement, version):
            success_count += 1
    
    print(f"\n✓ Successfully updated {success_count}/{total_files} files")
    
    if success_count == total_files:
        print(f"All version numbers updated to {version}")
        sys.exit(0)
    else:
        print("Warning: Not all files were updated successfully")
        sys.exit(1)


if __name__ == "__main__":
    main()
