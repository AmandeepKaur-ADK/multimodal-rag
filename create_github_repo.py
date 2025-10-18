#!/usr/bin/env python3
"""
Script to create GitHub repository and deploy AI Assistant
"""

import os
import subprocess
import sys

def run_command(cmd):
    """Run command and return result."""
    print(f"🔄 {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    print(f"✅ Success: {result.stdout.strip()}")
    return True

def main():
    print("🚀 GitHub Repository Creator for AI Assistant")
    print("=" * 50)
    
    # Get repository details
    repo_name = input("Enter repository name (default: free-ai-assistant): ").strip()
    if not repo_name:
        repo_name = "free-ai-assistant"
    
    username = input("Enter your GitHub username: ").strip()
    if not username:
        print("❌ GitHub username is required")
        sys.exit(1)
    
    print(f"\n📦 Creating repository: {username}/{repo_name}")
    
    # Check if git is configured
    print("\n🔧 Checking Git configuration...")
    if not run_command("git config user.name"):
        name = input("Enter your name for Git: ")
        run_command(f'git config user.name "{name}"')
    
    if not run_command("git config user.email"):
        email = input("Enter your email for Git: ")
        run_command(f'git config user.email "{email}"')
    
    # Add remote origin
    print(f"\n🔗 Adding GitHub remote...")
    remote_url = f"https://github.com/{username}/{repo_name}.git"
    run_command(f"git remote add origin {remote_url}")
    
    # Create final commit
    print("\n📝 Creating final commit...")
    run_command("git add .")
    run_command('git commit -m "Ready for deployment - Free AI Assistant"')
    
    print(f"\n🎉 Setup complete!")
    print(f"📋 Next steps:")
    print(f"1. Go to https://github.com/new")
    print(f"2. Create repository named: {repo_name}")
    print(f"3. Make it public")
    print(f"4. Don't initialize with README (we have one)")
    print(f"5. Run: git push -u origin main")
    print(f"\n🚀 Deploy URLs:")
    print(f"• Heroku: https://heroku.com/deploy?template=https://github.com/{username}/{repo_name}")
    print(f"• Railway: Connect at https://railway.app/new")
    print(f"• Render: Connect at https://render.com/")

if __name__ == "__main__":
    main()