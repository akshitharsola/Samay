# 🛠️ Samay v6 Setup Guide

## Prerequisites

### Required Software
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Chrome/Chromium browser** (for extension)
- **Ollama** with Phi-3-Mini model

### Ollama Setup
```bash
# Install Ollama (if not installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull Phi-3-Mini model
ollama pull phi3:mini

# Verify installation
ollama list
```

## Installation

### 1. Project Setup
```bash
# Navigate to project directory
cd /Users/akshitharsola/Documents/Samay/samay-v6

# Install root dependencies
npm install
```

### 2. Backend Setup
```bash
# Navigate to backend
cd web-app/backend

# Install Python dependencies
pip install -r requirements.txt

# Start backend server
python main.py
```
**Backend will run on**: http://localhost:8000

### 3. Frontend Setup
```bash
# Open new terminal and navigate to frontend
cd web-app/frontend

# Install React dependencies
npm install

# Start development server
npm start
```
**Frontend will run on**: http://localhost:3000

### 4. Extension Setup
1. **Open Chrome** and navigate to `chrome://extensions/`
2. **Enable Developer mode** (toggle in top-right)
3. **Click "Load unpacked"**
4. **Select the `extension/` folder** from samay-v6 project
5. **Verify extension is loaded** and shows as active

## Verification

### Check All Services
1. **Backend Health**: Visit http://localhost:8000/health
2. **Frontend Loading**: Visit http://localhost:3000
3. **Extension Active**: Check Chrome extensions page
4. **Ollama Running**: Run `ollama list` in terminal

### Test Communication
1. Open web app at http://localhost:3000
2. Type a test query
3. Check browser console for extension communication logs
4. Verify no errors in backend terminal

## Development Workflow

### Start All Services
```bash
# Option 1: Use the convenience script
npm run dev

# Option 2: Manual start (recommended for debugging)
# Terminal 1: Backend
cd web-app/backend && python main.py

# Terminal 2: Frontend  
cd web-app/frontend && npm start

# Terminal 3: Ollama (if not running as service)
ollama serve
```

### Extension Development
- **Reload extension**: Go to chrome://extensions/ and click reload button
- **Debug extension**: Right-click extension icon → "Inspect popup"
- **View background script logs**: Extensions page → "Inspect views: background page"

## Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.8+

# Check if port 8000 is in use
lsof -i :8000

# Install dependencies in virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend Won't Start
```bash
# Check Node.js version
node --version  # Should be 16+

# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Extension Not Loading
- **Check manifest.json syntax**: Use JSON validator
- **Verify file permissions**: Extension folder should be readable
- **Check Chrome version**: Manifest V3 requires Chrome 88+
- **Look for errors**: Check Extensions page for error messages

#### Ollama Issues
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama service
ollama serve

# Re-pull model if corrupted
ollama rm phi3:mini
ollama pull phi3:mini
```

### Debug Modes

#### Enable Verbose Logging
```bash
# Backend debug mode
DEBUG=1 python main.py

# Frontend debug mode
REACT_APP_DEBUG=1 npm start
```

#### Extension Debug
1. Open extension popup and press F12
2. Check background script in Extensions page
3. Enable console logging in extension code

## Configuration

### Environment Variables
Create `.env` files as needed:

**Backend (.env)**:
```
DEBUG=false
LOG_LEVEL=info
OLLAMA_URL=http://localhost:11434
```

**Frontend (.env)**:
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_DEBUG=false
```

### Extension Permissions
The extension requires these permissions:
- **scripting**: For injecting automation scripts
- **tabs**: For managing AI service tabs
- **storage**: For saving preferences
- **activeTab**: For current tab access
- **Host permissions**: For ChatGPT, Claude, Gemini, Perplexity domains

## Next Steps
Once setup is complete, see:
- [Architecture Guide](ARCHITECTURE.md) - Understand system design
- [API Reference](API_REFERENCE.md) - Backend API documentation
- [User Guide](../README.md) - How to use the system