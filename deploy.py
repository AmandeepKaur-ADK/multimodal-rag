#!/usr/bin/env python3
"""
Deployment script for Free AI Assistant
Supports multiple deployment platforms
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_command(cmd, check=True):
    """Run shell command and return result."""
    print(f"🔄 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {result.stderr}")
        sys.exit(1)
    
    return result

def check_requirements():
    """Check if all requirements are met."""
    print("🔍 Checking deployment requirements...")
    
    # Check if git is initialized
    if not Path('.git').exists():
        print("❌ Git repository not initialized")
        return False
    
    # Check if required files exist
    required_files = [
        'web_app.py', 'requirements.txt', 'Procfile', 
        'templates/index.html', 'src/free_rag_pipeline.py'
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Required file missing: {file}")
            return False
    
    print("✅ All requirements met!")
    return True

def deploy_to_heroku():
    """Deploy to Heroku."""
    print("\n🚀 Deploying to Heroku...")
    
    # Check if Heroku CLI is installed
    result = run_command("heroku --version", check=False)
    if result.returncode != 0:
        print("❌ Heroku CLI not installed. Please install it first:")
        print("   https://devcenter.heroku.com/articles/heroku-cli")
        return False
    
    # Login to Heroku
    print("🔐 Please login to Heroku...")
    run_command("heroku login")
    
    # Create Heroku app
    app_name = input("Enter your Heroku app name (or press Enter for auto-generated): ").strip()
    
    if app_name:
        run_command(f"heroku create {app_name}")
    else:
        run_command("heroku create")
    
    # Set environment variables
    run_command("heroku config:set FLASK_ENV=production")
    run_command("heroku config:set FLASK_DEBUG=False")
    
    # Deploy
    run_command("git push heroku main")
    
    # Open the app
    run_command("heroku open")
    
    print("✅ Heroku deployment complete!")
    return True

def deploy_to_railway():
    """Deploy to Railway."""
    print("\n🚀 Deploying to Railway...")
    
    # Check if Railway CLI is installed
    result = run_command("railway --version", check=False)
    if result.returncode != 0:
        print("❌ Railway CLI not installed. Installing...")
        run_command("npm install -g @railway/cli")
    
    # Login to Railway
    print("🔐 Please login to Railway...")
    run_command("railway login")
    
    # Initialize Railway project
    run_command("railway init")
    
    # Deploy
    run_command("railway up")
    
    print("✅ Railway deployment complete!")
    return True

def deploy_to_render():
    """Instructions for Render deployment."""
    print("\n🚀 Render Deployment Instructions:")
    print("1. Go to https://render.com and create an account")
    print("2. Connect your GitHub repository")
    print("3. Create a new Web Service")
    print("4. Use these settings:")
    print("   - Build Command: pip install -r requirements.txt")
    print("   - Start Command: gunicorn --bind 0.0.0.0:$PORT web_app:app")
    print("   - Environment: Python 3")
    print("5. Add environment variables:")
    print("   - FLASK_ENV=production")
    print("   - FLASK_DEBUG=False")
    print("6. Deploy!")
    
    return True

def create_github_repo():
    """Create GitHub repository."""
    print("\n📦 Creating GitHub repository...")
    
    # Check if GitHub CLI is installed
    result = run_command("gh --version", check=False)
    if result.returncode != 0:
        print("❌ GitHub CLI not installed. Please:")
        print("1. Go to https://github.com/new")
        print("2. Create a new repository")
        print("3. Follow the instructions to push your code")
        return False
    
    # Create repository
    repo_name = input("Enter repository name: ").strip()
    if not repo_name:
        repo_name = "free-ai-assistant"
    
    description = "Free AI Assistant with web search - No API keys required!"
    
    run_command(f'gh repo create {repo_name} --public --description "{description}" --push')
    
    print(f"✅ GitHub repository created: https://github.com/$(gh api user --jq .login)/{repo_name}")
    return True

def main():
    """Main deployment function."""
    print("🤖 Free AI Assistant - Deployment Tool")
    print("=" * 50)
    
    if not check_requirements():
        sys.exit(1)
    
    print("\nDeployment Options:")
    print("1. 📦 Create GitHub Repository")
    print("2. 🚀 Deploy to Heroku")
    print("3. 🚄 Deploy to Railway")
    print("4. 🎨 Deploy to Render (instructions)")
    print("5. 🐳 Docker Build")
    print("6. 📋 Show all deployment info")
    
    choice = input("\nSelect option (1-6): ").strip()
    
    if choice == "1":
        create_github_repo()
    elif choice == "2":
        deploy_to_heroku()
    elif choice == "3":
        deploy_to_railway()
    elif choice == "4":
        deploy_to_render()
    elif choice == "5":
        print("🐳 Building Docker image...")
        run_command("docker build -t free-ai-assistant .")
        print("✅ Docker image built! Run with:")
        print("   docker run -p 5000:5000 free-ai-assistant")
    elif choice == "6":
        print("\n📋 All Deployment Options:")
        print("\n🔗 Quick Deploy Links:")
        print("• Heroku: https://dashboard.heroku.com/new-app")
        print("• Railway: https://railway.app/new")
        print("• Render: https://render.com/")
        print("• Vercel: https://vercel.com/new")
        print("• Netlify: https://app.netlify.com/start")
        
        print("\n🚀 One-Click Deploy Buttons (add to README):")
        print("[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)")
        print("[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)")
    else:
        print("❌ Invalid option")
        sys.exit(1)
    
    print("\n🎉 Deployment process complete!")
    print("📖 Check README.md for more deployment options")

if __name__ == "__main__":
    main()