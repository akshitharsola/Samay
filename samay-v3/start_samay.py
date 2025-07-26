#!/usr/bin/env python3
"""
Samay v3 - Startup Script
=========================
Unified startup script for both CLI and Web UI modes
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import websockets
        import requests
        from orchestrator.manager import SamaySessionManager
        print("✅ All Python dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Run: pip install -r requirements.txt")
        return False

def check_ollama():
    """Check if Ollama is running with phi3:mini model"""
    print("🔍 Checking Ollama and phi3:mini model...")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            phi3_found = any("phi3:mini" in model.get("name", "") for model in models)
            if phi3_found:
                print("✅ Ollama running with phi3:mini model")
                return True
            else:
                print("⚠️  Ollama running but phi3:mini model not found")
                print("📦 Run: ollama pull phi3:mini")
                return False
        else:
            print("❌ Ollama not responding")
            return False
    except Exception as e:
        print(f"❌ Ollama check failed: {e}")
        print("🚀 Start Ollama: brew services start ollama")
        print("📦 Install model: ollama pull phi3:mini")
        return False

def start_web_mode():
    """Start the web interface mode"""
    print("\n🌐 Starting Samay v3 Web Interface...")
    print("=" * 50)
    
    # Check if Node.js frontend should be started
    frontend_dir = Path("frontend")
    if frontend_dir.exists() and (frontend_dir / "package.json").exists():
        print("📋 Frontend detected, starting React development server...")
        
        # Start backend in background
        print("🚀 Starting FastAPI backend...")
        backend_process = subprocess.Popen([
            sys.executable, "web_api.py"
        ], cwd=Path.cwd())
        
        # Give backend time to start
        time.sleep(3)
        
        # Start frontend
        print("🎨 Starting React frontend...")
        try:
            frontend_process = subprocess.run([
                "npm", "start"
            ], cwd=frontend_dir, check=True)
        except subprocess.CalledProcessError:
            print("❌ Frontend failed to start")
            print("📦 Try: cd frontend && npm install && npm start")
        except FileNotFoundError:
            print("❌ Node.js not found")
            print("📦 Install Node.js: https://nodejs.org/")
        
        # Cleanup
        backend_process.terminate()
    
    else:
        # Just start the backend with built-in UI
        print("🚀 Starting FastAPI backend with built-in UI...")
        subprocess.run([sys.executable, "web_api.py"])

def start_cli_mode():
    """Start the CLI interface mode"""
    print("\n🖥️  Starting Samay v3 CLI Interface...")
    print("=" * 50)
    subprocess.run([sys.executable, "samay.py"])

def main():
    """Main startup function"""
    print("🤖 Samay v3 - Multi-Agent AI Assistant")
    print("=" * 60)
    print("🔬 Research-based solution for persistent AI sessions")
    print("🛡️  Anti-bot protection + Profile persistence + Local LLM")
    print()
    
    # Check system requirements
    if not check_dependencies():
        sys.exit(1)
    
    if not check_ollama():
        print("\n⚠️  Local LLM not available, but cloud services will still work")
        print("Press Enter to continue anyway, or Ctrl+C to exit...")
        try:
            input()
        except KeyboardInterrupt:
            sys.exit(1)
    
    print("\n🎛️  Select Interface Mode:")
    print("1. 🌐 Web Interface (Modern UI with real-time chat)")
    print("2. 🖥️  CLI Interface (Command-line interface)")
    print("3. ❌ Exit")
    
    while True:
        choice = input("\nSelect mode (1-3): ").strip()
        
        if choice == "1":
            start_web_mode()
            break
        elif choice == "2":
            start_cli_mode()
            break
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice, please try again")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Samay v3 stopped by user")
    except Exception as e:
        print(f"\n❌ Startup error: {e}")
        sys.exit(1)