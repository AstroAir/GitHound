#!/usr/bin/env python3
"""
Test script for GitHound enhanced web interface.
This script starts the web server and opens the interface in the browser.
"""

import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path

def main():
    """Start the GitHound web interface and open it in the browser."""
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    print("🐕 GitHound Enhanced Web Interface Test")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not (project_root / "githound").exists():
        print("❌ Error: Not in GitHound project directory")
        sys.exit(1)
    
    print(f"📁 Project root: {project_root}")
    print(f"🌐 Web files: {project_root / 'githound' / 'web' / 'static'}")
    
    # Check if static files exist
    static_dir = project_root / "githound" / "web" / "static"
    required_files = ["index.html", "style.css", "app.js"]
    
    for file in required_files:
        file_path = static_dir / file
        if file_path.exists():
            print(f"✅ {file} found")
        else:
            print(f"❌ {file} missing")
            sys.exit(1)
    
    print("\n🚀 Starting GitHound web server...")
    
    try:
        # Start the web server
        cmd = [sys.executable, "-m", "githound.web.main"]
        print(f"📝 Command: {' '.join(cmd)}")
        
        # Start the server process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for the server to start
        print("⏳ Waiting for server to start...")
        time.sleep(3)
        
        # Check if the process is still running
        if process.poll() is None:
            print("✅ Server started successfully!")
            
            # Open the browser
            url = "http://localhost:8000"
            print(f"🌐 Opening {url} in browser...")
            webbrowser.open(url)
            
            print("\n" + "=" * 50)
            print("🎉 GitHound Web Interface is now running!")
            print(f"📍 URL: {url}")
            print("🔧 Press Ctrl+C to stop the server")
            print("=" * 50)
            
            # Wait for the process to complete or be interrupted
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping server...")
                process.terminate()
                process.wait()
                print("✅ Server stopped")
                
        else:
            # Process failed to start
            stdout, stderr = process.communicate()
            print("❌ Failed to start server")
            print(f"📤 stdout: {stdout}")
            print(f"📥 stderr: {stderr}")
            sys.exit(1)
            
    except FileNotFoundError:
        print("❌ Error: Python not found or GitHound not installed")
        print("💡 Try: pip install -e .")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
