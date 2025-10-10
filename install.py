#!/usr/bin/env python3
"""
XIBE-CHAT CLI Installation Script
"""

import subprocess
import sys
import os
from pathlib import Path

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

def install_xibe_chat():
    """Install XIBE-CHAT CLI from PyPI."""
    print("🚀 Installing XIBE-CHAT CLI...")
    
    # Check if pip is available
    if not run_command("pip --version", "Checking pip"):
        print("❌ pip is not available. Please install Python and pip first.")
        return False
    
    # Upgrade pip
    run_command("python -m pip install --upgrade pip", "Upgrading pip")
    
    # Install XIBE-CHAT CLI
    if run_command("pip install xibe-chat-cli", "Installing XIBE-CHAT CLI"):
        print("\n🎉 XIBE-CHAT CLI installed successfully!")
        print("\n📖 Usage:")
        print("  xibe-chat    # Start the CLI")
        print("  xibe         # Short alias")
        print("\n💡 Tips:")
        print("  - Use 'xibe-chat --help' for help")
        print("  - Use '/help' inside the CLI for all commands")
        print("  - Set API_TOKEN environment variable for better rate limits")
        return True
    else:
        print("❌ Installation failed. Please check the error messages above.")
        return False

def update_xibe_chat():
    """Update XIBE-CHAT CLI to the latest version."""
    print("🔄 Updating XIBE-CHAT CLI...")
    
    if run_command("pip install --upgrade xibe-chat-cli", "Updating XIBE-CHAT CLI"):
        print("✅ XIBE-CHAT CLI updated successfully!")
        return True
    else:
        print("❌ Update failed. Please check the error messages above.")
        return False

def main():
    """Main installation function."""
    print("=" * 60)
    print("🎯 XIBE-CHAT CLI Installer")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "update":
        return update_xibe_chat()
    else:
        return install_xibe_chat()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
