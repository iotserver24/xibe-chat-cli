#!/usr/bin/env python3
"""
Version update script for XIBE-CHAT CLI
Updates version in ai_cli.py, setup.py, and pyproject.toml
"""

import re
import sys
import argparse


def update_version_in_file(file_path, old_pattern, new_pattern, new_version):
    """Update version in a file using regex patterns."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        updated_content = re.sub(old_pattern, new_pattern.format(version=new_version), content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"✅ Updated {file_path} to version {new_version}")
        return True
    except (IOError, OSError) as e:
        print(f"❌ Error updating {file_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Update version in all project files')
    parser.add_argument('version', help='New version number (e.g., 0.8.9)')
    args = parser.parse_args()

    new_version = args.version

    # Validate version format
    if not re.match(r'^\d+\.\d+\.\d+$', new_version):
        print("❌ Invalid version format. Please use format: x.x.x (e.g., 0.8.9)")
        sys.exit(1)

    print(f"🔄 Updating version to {new_version} in all files...")

    # Update ai_cli.py
    success1 = update_version_in_file(
        'ai_cli.py',
        r'CURRENT_VERSION = "[^"]*"',
        'CURRENT_VERSION = "{version}"',
        new_version
    )

    # Update setup.py
    success2 = update_version_in_file(
        'setup.py',
        r'    version="[^"]*",',
        '    version="{version}",',
        new_version
    )

    # Update pyproject.toml
    success3 = update_version_in_file(
        'pyproject.toml',
        r'version = "[^"]*"',
        'version = "{version}"',
        new_version
    )

    if success1 and success2 and success3:
        print(f"🎉 Successfully updated all files to version {new_version}!")
        return 0
    else:
        print("❌ Some files failed to update. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
