# 🚀 Samay v6: Browser Extension Multi-AI Automation

**Next-generation AI productivity tool with browser extension automation**

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Chrome/Chromium browser
- Ollama with Phi-3-Mini model

### Setup
```bash
# Clone and navigate
cd samay-v6

# Backend setup
cd web-app/backend
pip install -r requirements.txt
python main.py

# Frontend setup (new terminal)
cd web-app/frontend
npm install
npm start

# Load extension
# Open Chrome → Extensions → Developer mode → Load unpacked → select extension/
```

### Usage
1. Open web app: http://localhost:3000
2. Ensure extension is loaded and active
3. Type your query and click "Automate"
4. Watch as all 4 AI services are automated simultaneously
5. Receive synthesized response in 30-90 seconds

## Features
- ✅ **Zero API Costs** - Uses free web interfaces
- ✅ **One-Click Automation** - Query → 4 AI responses automatically
- ✅ **Intelligent Follow-ups** - Automated multi-turn conversations
- ✅ **Local Processing** - All synthesis done locally
- ✅ **Cross-Domain Automation** - Browser extension bypasses security limitations

## Architecture
- **Web App**: React frontend + FastAPI backend
- **Extension**: Manifest V3 Chrome extension
- **Local LLM**: Ollama Phi-3-Mini for synthesis
- **Services**: ChatGPT, Claude, Gemini, Perplexity

## Documentation
- [Setup Guide](docs/SETUP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)

---
**Innovation**: True multi-AI automation without paid APIs