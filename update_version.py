#!/usr/bin/env python3
"""
Script to update version in all project files
"""
import sys
import re


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
    except Exception as e:
        print(f"✗ Error updating {filepath}: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <version>")
        print("Example: python update_version.py 0.8.9")
        sys.exit(1)
    
    version = sys.argv[1]
    
    # Validate version format (basic check)
    if not re.match(r'^\d+\.\d+\.\d+$', version):
        print(f"Error: Invalid version format '{version}'. Expected format: X.Y.Z")
        sys.exit(1)
    
    print(f"Updating version to {version}...")
    
    success_count = 0
    
    # Update ai_cli.py
    if update_version_in_file(
        'ai_cli.py',
        r'CURRENT_VERSION = "[^"]*"',
        'CURRENT_VERSION = "{version}"',
        version
    ):
        success_count += 1
    
    # Update setup.py
    if update_version_in_file(
        'setup.py',
        r'version="[^"]*"',
        'version="{version}"',
        version
    ):
        success_count += 1
    
    # Update pyproject.toml
    if update_version_in_file(
        'pyproject.toml',
        r'version = "[^"]*"',
        'version = "{version}"',
        version
    ):
        success_count += 1
    
    print(f"\n✓ Successfully updated {success_count}/3 files")
    
    if success_count == 3:
        print(f"All version numbers updated to {version}")
        sys.exit(0)
    else:
        print("Warning: Not all files were updated successfully")
        sys.exit(1)


if __name__ == "__main__":
    main()
