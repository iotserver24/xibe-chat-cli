#!/usr/bin/env python3
"""
Manual PyPI Upload Script for XIBE-CHAT CLI
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def upload_to_pypi():
    """Upload XIBE-CHAT CLI to PyPI."""
    print("🚀 Uploading XIBE-CHAT CLI to PyPI...")
    
    # Check if twine is available
    if not run_command("twine --version", "Checking twine"):
        print("📦 Installing twine...")
        run_command("pip install twine", "Installing twine")
    
    # Build the package
    if not run_command("python -m build", "Building package"):
        return False
    
    # Check the package
    if not run_command("twine check dist/*", "Checking package"):
        return False
    
    print("\n📤 Ready to upload to PyPI!")
    print("Choose upload method:")
    print("1. Test PyPI (recommended for first upload)")
    print("2. Production PyPI")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        # Upload to test PyPI first
        print("\n🧪 Uploading to Test PyPI...")
        print("URL: https://test.pypi.org/project/xibe-chat-cli/")
        if run_command("twine upload --repository testpypi dist/*", "Uploading to Test PyPI"):
            print("\n✅ Uploaded to Test PyPI successfully!")
            print("🔗 View at: https://test.pypi.org/project/xibe-chat-cli/")
            print("\n📋 Test installation:")
            print("pip install --index-url https://test.pypi.org/simple/ xibe-chat-cli")
            
            # Ask if they want to upload to production
            upload_prod = input("\nUpload to production PyPI? (y/N): ").strip().lower()
            if upload_prod == 'y':
                return upload_to_production()
            else:
                print("✅ Upload complete! Test PyPI only.")
                return True
        else:
            return False
            
    elif choice == "2":
        return upload_to_production()
    else:
        print("❌ Invalid choice. Please run the script again.")
        return False

def upload_to_production():
    """Upload to production PyPI."""
    print("\n🚀 Uploading to Production PyPI...")
    print("URL: https://pypi.org/project/xibe-chat-cli/")
    
    if run_command("twine upload dist/*", "Uploading to Production PyPI"):
        print("\n🎉 Uploaded to Production PyPI successfully!")
        print("🔗 View at: https://pypi.org/project/xibe-chat-cli/")
        print("\n📋 Installation command for users:")
        print("pip install xibe-chat-cli")
        print("xibe-chat")
        return True
    else:
        return False

def main():
    """Main upload function."""
    print("=" * 60)
    print("🎯 XIBE-CHAT CLI PyPI Uploader")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("setup.py"):
        print("❌ setup.py not found. Please run this script from the project root.")
        return False
    
    # Check if dist directory exists
    if not os.path.exists("dist"):
        print("📦 dist/ directory not found. Building package first...")
        if not run_command("python -m build", "Building package"):
            return False
    
    return upload_to_pypi()

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Upload completed successfully!")
    else:
        print("\n❌ Upload failed. Please check the error messages above.")
    sys.exit(0 if success else 1)
