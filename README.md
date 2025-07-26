# Samay - Multi-Agent AI Assistant Platform

🚀 **Complete AI session management solution with persistent, anti-bot resistant sessions**

## 🎯 Project Overview

Samay is a comprehensive multi-agent AI assistant platform that solves the persistent problem of maintaining authenticated sessions across multiple AI services. Built with advanced anti-bot detection bypass and automated session management.

## 📁 Project Structure

```
Samay/
├── samay-v3/                 # Core session manager (Python)
│   ├── orchestrator/         # Main driver and validation logic
│   ├── otp_service/          # Automated OTP handling
│   ├── profiles/             # Persistent browser profiles
│   └── frontend/             # React-based UI dashboard
├── samay-ui/                 # Standalone React UI components
├── INFORMATION/              # Project documentation & research
├── test-results/             # Testing artifacts
└── README.md                # This file
```

## 🔧 Core Components

### 1. **Samay v3** - Main Session Manager
- **Anti-bot protection** with SeleniumBase UC Mode
- **Persistent sessions** across computer restarts
- **Automated OTP fetching** via Gmail API
- **Multi-service support** (Claude, Gemini, Perplexity)

### 2. **Modern React UI**
- Real-time session monitoring dashboard
- Service health status indicators
- Interactive setup wizard
- Responsive design with Tailwind CSS

### 3. **Research Documentation**
- Comprehensive implementation plans
- Anti-bot detection research
- Session persistence techniques
- Performance optimization strategies

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ with conda environment
- Node.js 16+ for React UI
- Chrome browser for UC Mode profiles
- Gmail API credentials for OTP automation

### Installation

```bash
# Clone the repository
git clone https://github.com/akshitharsola/Samay.git
cd Samay

# Set up the core session manager
cd samay-v3
source /opt/anaconda3/bin/activate samay
pip install -r requirements.txt

# Set up the React UI
cd frontend
npm install
```

### Configuration

1. **Environment Setup**
   ```bash
   # Copy and edit .env file
   cp samay-v3/.env.example samay-v3/.env
   # Add your email and proxy settings
   ```

2. **Gmail API Setup**
   - Create Google Cloud project
   - Enable Gmail API
   - Download credentials.json
   - Place in `samay-v3/otp_service/secrets/`

3. **First Run**
   ```bash
   # Start the session manager
   cd samay-v3
   python orchestrator/manager.py
   
   # In another terminal, start the UI
   cd frontend
   npm start
   ```

## 🛡️ Key Features

### ✅ **Session Persistence**
- UC Mode generated profiles survive restarts
- Automatic session validation and recovery
- Cross-platform compatibility (macOS focus)

### ✅ **Anti-Bot Protection**
- Advanced fingerprint spoofing
- Human-like interaction patterns
- Residential proxy support

### ✅ **Automation**
- Zero-touch OTP retrieval
- Intelligent session monitoring
- Automatic re-authentication flows

### ✅ **Multi-Service Support**
- Claude (Anthropic)
- Gemini (Google)
- Perplexity AI
- Extensible architecture for new services

## 🤖 AI Models

This project uses **Ollama** for local AI processing and model management.

> **Note**: Ollama model files are not included in this repository due to size constraints (typically 4-7GB per model). You need to install Ollama separately and pull the required models:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended models for this project
ollama pull llama2          # General purpose
ollama pull codellama       # Code assistance
ollama pull mistral         # Lightweight alternative
```

**Recommended Models for MacBook Air M2 8GB:**
- **llama2:7b** - Best balance of performance and memory usage
- **mistral:7b** - Fast inference, good for quick responses
- **codellama:7b** - Specialized for code-related tasks

## 📊 System Requirements

- **RAM**: 8GB minimum (16GB recommended for larger models)
- **Storage**: 20GB+ free space for models and profiles
- **CPU**: Apple Silicon M1/M2 (Intel compatible but slower)
- **Network**: Stable internet for API calls and model downloads

## 🔍 Troubleshooting

### Common Issues

1. **Profile Issues**
   ```bash
   # Reset corrupted profiles
   cd samay-v3
   python orchestrator/manager.py
   # → Option 5: Reset service
   ```

2. **OTP Not Working**
   ```bash
   # Test Gmail API connection
   python otp_service/gmail_fetcher.py
   # → Option 1: Test connection
   ```

3. **UI Connection Issues**
   ```bash
   # Check backend API status
   cd samay-v3
   python web_api.py
   # Should start on http://localhost:5000
   ```

## 📈 Development Status

- ✅ **Core Session Management** - Production ready
- ✅ **React UI Dashboard** - Feature complete
- ✅ **OTP Automation** - Stable
- 🔄 **Multi-Agent Orchestration** - In development
- 🔄 **Response Aggregation** - Planned
- 🔄 **Docker Deployment** - Planned

## 🎉 Success Metrics

When properly configured:
1. **Browser opens with persistent profiles** (not guest mode)
2. **Sessions survive computer restarts** (no re-login required)
3. **Health check shows all services active**
4. **OTP codes retrieved automatically**
5. **UI dashboard shows real-time status**

## 📝 Documentation

Comprehensive documentation available in the `INFORMATION/` directory:

- **Implementation Plans** - Detailed technical specifications
- **Research Findings** - Anti-bot detection solutions
- **Architecture Overview** - System design and components
- **Performance Analysis** - Optimization techniques

## 🤝 Contributing

This is a personal research project. Feel free to fork and adapt for your needs.

## 📄 License

MIT License - see individual component directories for specific licensing.

---

**🚀 Start here**: `cd samay-v3 && python orchestrator/manager.py`

Built with ❤️ for persistent AI session management on macOS