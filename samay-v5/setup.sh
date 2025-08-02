#!/bin/bash

# Samay v5 Setup Script
# One-command setup for development environment

set -e

echo "🚀 Setting up Samay v5 - Next-Generation AI Assistant"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11+ is installed
check_python() {
    print_status "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    REQUIRED_VERSION="3.11"
    
    if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
        print_error "Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION or higher is required."
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION found"
}

# Check if Node.js is installed
check_nodejs() {
    print_status "Checking Node.js version..."
    
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed. Frontend development will not be available."
        print_warning "Please install Node.js 18+ for full functionality."
        return 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2)
    REQUIRED_NODE_VERSION="18.0.0"
    
    if [ "$(printf '%s\n' "$REQUIRED_NODE_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_NODE_VERSION" ]; then
        print_warning "Node.js $NODE_VERSION found, but Node.js 18+ is recommended."
    else
        print_success "Node.js $NODE_VERSION found"
    fi
    
    return 0
}

# Check if Ollama is installed
check_ollama() {
    print_status "Checking Ollama installation..."
    
    if ! command -v ollama &> /dev/null; then
        print_warning "Ollama is not installed."
        print_warning "Local assistant will not work without Ollama."
        print_warning "Install from: https://ollama.ai"
        return 1
    fi
    
    print_success "Ollama found"
    
    # Check if Phi-3-Mini model is available
    print_status "Checking for Phi-3-Mini model..."
    if ollama list | grep -q "phi3:mini"; then
        print_success "Phi-3-Mini model is available"
    else
        print_warning "Phi-3-Mini model not found. Pulling model..."
        ollama pull phi3:mini
        print_success "Phi-3-Mini model installed"
    fi
    
    return 0
}

# Setup Python environment (use samay-v5 conda env or create new venv)
setup_python_env() {
    print_status "Setting up Python environment..."
    
    # Check if samay-v5 conda environment exists
    if command -v conda &> /dev/null && conda env list | grep -q "samay-v5"; then
        print_status "Found conda environment 'samay-v5'"
        eval "$(conda shell.bash hook)"
        conda activate samay-v5
        
    # Check if samay conda environment exists with Python 3.11+
    elif command -v conda &> /dev/null && conda env list | grep -q "samay"; then
        print_status "Found conda environment 'samay'"
        eval "$(conda shell.bash hook)"
        conda activate samay
        
        # Check Python version in this environment
        PYTHON_VERSION=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        REQUIRED_VERSION="3.11"
        
        if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
            print_warning "Python $PYTHON_VERSION found in samay environment, but Python $REQUIRED_VERSION+ is required."
            print_status "Creating new samay-v5 conda environment with Python 3.13..."
            conda create -n samay-v5 python=3.13 -y
            conda activate samay-v5
        fi
        
    # Check if samay virtual environment exists
    elif [ -d "../samay" ] || [ -d "../../samay" ] || [ -d "../../../samay" ]; then
        print_status "Found existing 'samay' virtual environment"
        
        # Try to find and activate samay venv
        if [ -d "../samay" ]; then
            SAMAY_VENV="../samay"
        elif [ -d "../../samay" ]; then
            SAMAY_VENV="../../samay"
        elif [ -d "../../../samay" ]; then
            SAMAY_VENV="../../../samay"
        fi
        
        print_status "Using existing samay virtual environment at: $SAMAY_VENV"
        source "$SAMAY_VENV/bin/activate"
        
    else
        print_warning "No existing 'samay' environment found"
        print_status "Creating new virtual environment with Python 3.13..."
        python3 -m venv venv
        source venv/bin/activate
        print_success "New virtual environment created"
    fi
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
}

# Create directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p storage
    mkdir -p logs
    mkdir -p screenshots
    mkdir -p profiles/claude
    mkdir -p profiles/gemini  
    mkdir -p profiles/perplexity
    
    print_success "Directories created"
}

# Setup environment variables
setup_env() {
    print_status "Setting up environment variables..."
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        print_success "Environment file created from template"
        print_warning "Please edit .env file with your API keys"
    else
        print_status "Environment file already exists"
    fi
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    # Create empty database files
    touch storage/credentials.db
    touch storage/sessions.db
    touch storage/conversations.db
    
    print_success "Database files initialized"
}

# Setup frontend (if Node.js is available)
setup_frontend() {
    print_status "Setting up frontend..."
    
    if check_nodejs; then
        # Create basic React frontend structure
        if [ ! -d "frontend/node_modules" ]; then
            cd frontend
            npm install
            cd ..
            print_success "Frontend dependencies installed"
        else
            print_status "Frontend dependencies already installed"
        fi
    else
        print_warning "Skipping frontend setup (Node.js not available)"
    fi
}

# Create test script
create_test_script() {
    print_status "Creating test script..."
    
    cat > test_samay.py << 'EOF'
#!/usr/bin/env python3
"""
Simple test script for Samay v5
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append('.')

from core.local_assistant import LocalAssistant
from core.api_manager import APIServiceManager
from core.session_manager import SessionManager

async def test_components():
    """Test core components"""
    print("🧪 Testing Samay v5 Components")
    print("=" * 40)
    
    try:
        # Test API Manager
        print("Testing API Manager...")
        api_manager = APIServiceManager()
        status = api_manager.get_service_status()
        print(f"✅ API Manager: {len(status)} services configured")
        
        # Test Session Manager
        print("Testing Session Manager...")
        session_manager = SessionManager()
        session_id = session_manager.create_session("test_user")
        print(f"✅ Session Manager: Created session {session_id}")
        
        # Test Local Assistant (if Ollama is available)
        print("Testing Local Assistant...")
        try:
            assistant = LocalAssistant()
            print("✅ Local Assistant: Initialized successfully")
            
            # Simple test query
            context = await assistant.discuss_and_refine("What is 2+2?", "test_user")
            print(f"✅ Local Assistant: Query processed, stage: {context.stage}")
            
        except Exception as e:
            print(f"⚠️  Local Assistant: {e}")
            print("   (This is expected if Ollama is not running)")
        
        print("\n🎉 Core components test completed!")
        print("You can now start the backend with: python backend/main.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_components())
EOF
    
    chmod +x test_samay.py
    print_success "Test script created"
}

# Create start script
create_start_script() {
    print_status "Creating start script..."
    
    cat > start_samay.sh << 'EOF'
#!/bin/bash

# Start Samay v5 Development Environment

echo "🚀 Starting Samay v5"
echo "=================="

# Activate virtual environment
if command -v conda &> /dev/null && conda env list | grep -q "samay-v5"; then
    eval "$(conda shell.bash hook)"
    conda activate samay-v5
elif command -v conda &> /dev/null && conda env list | grep -q "samay"; then
    eval "$(conda shell.bash hook)"
    conda activate samay
elif [ -d "../samay" ]; then
    source "../samay/bin/activate"
elif [ -d "../../samay" ]; then
    source "../../samay/bin/activate"  
elif [ -d "../../../samay" ]; then
    source "../../../samay/bin/activate"
elif [ -d "venv" ]; then
    source "venv/bin/activate"
else
    echo "⚠️  No virtual environment found. Please check samay venv location."
    exit 1
fi

# Start Ollama in background (if available)
if command -v ollama &> /dev/null; then
    echo "Starting Ollama..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 2
fi

# Start backend
echo "Starting FastAPI backend..."
python backend/main.py &
BACKEND_PID=$!

# Start frontend (if available)
if [ -d "frontend/node_modules" ]; then
    echo "Starting React frontend..."
    cd frontend
    npm start &
    FRONTEND_PID=$!
    cd ..
fi

echo ""
echo "🎉 Samay v5 is starting up!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000 (if available)"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo "Stopping services..."; kill $BACKEND_PID 2>/dev/null; kill $FRONTEND_PID 2>/dev/null; kill $OLLAMA_PID 2>/dev/null; exit' INT
wait
EOF
    
    chmod +x start_samay.sh
    print_success "Start script created"
}

# Main setup function
main() {
    echo ""
    print_status "Starting Samay v5 setup process..."
    echo ""
    
    # Check prerequisites
    check_python
    check_nodejs
    check_ollama
    
    echo ""
    
    # Setup components
    create_directories
    setup_env
    setup_python_env
    init_database
    setup_frontend
    create_test_script
    create_start_script
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your API keys"
    echo "2. Run test: ./test_samay.py"
    echo "3. Start Samay: ./start_samay.sh"
    echo ""
    echo "For development:"
    echo "- Backend only: source venv/bin/activate && python backend/main.py"
    echo "- API Documentation: http://localhost:8000/docs"
    echo ""
    
    print_success "Samay v5 is ready! 🚀"
}

# Run main function
main