#!/usr/bin/env python3
"""
Quick Railway deployment script
"""

import subprocess
import sys
import webbrowser

def run_command(cmd, check=True):
    """Run command and return result."""
    print(f"🔄 {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    
    if result.stdout.strip():
        print(f"✅ {result.stdout.strip()}")
    return True

def main():
    print("🚄 Railway Deployment for AI Assistant")
    print("=" * 40)
    
    # Check if Railway CLI is installed
    print("🔍 Checking Railway CLI...")
    if not run_command("railway --version", check=False):
        print("📦 Installing Railway CLI...")
        if not run_command("npm install -g @railway/cli"):
            print("❌ Failed to install Railway CLI")
            print("💡 Please install Node.js first: https://nodejs.org")
            print("💡 Or deploy manually at: https://railway.app")
            return
    
    print("🔐 Logging into Railway...")
    print("📝 This will open your browser for authentication...")
    
    if not run_command("railway login"):
        print("❌ Railway login failed")
        return
    
    print("🚀 Initializing Railway project...")
    if not run_command("railway init"):
        print("❌ Railway init failed")
        return
    
    print("☁️ Deploying to Railway...")
    if not run_command("railway up"):
        print("❌ Railway deployment failed")
        return
    
    print("🌐 Getting deployment URL...")
    result = subprocess.run("railway status", shell=True, capture_output=True, text=True)
    
    print("\n🎉 Deployment Complete!")
    print("📋 Your AI Assistant is now live!")
    print("\n🔗 Access your app:")
    print("   • Run 'railway status' to get the URL")
    print("   • Or check Railway dashboard: https://railway.app/dashboard")
    
    print("\n📊 Test your deployment:")
    print("   • Health check: [YOUR_URL]/api/health")
    print("   • Ask question: [YOUR_URL]/api/ask")
    print("   • Web interface: [YOUR_URL]/")

if __name__ == "__main__":
    main()