# Samay - Multi-Agent AI Assistant Platform

🚀 **Complete AI session management solution with multi-version architecture evolution**

## 🎯 Project Overview

Samay is a comprehensive multi-agent AI assistant platform that has evolved through multiple architectural approaches to solve the persistent problem of maintaining authenticated sessions across multiple AI services. From browser automation to native applications to browser extensions, each version has pushed the boundaries of AI service integration.

## 📁 Project Structure

```
Samay/
├── samay-v3/                 # Core session manager (Python + SeleniumBase)
│   ├── orchestrator/         # Main driver and validation logic
│   ├── otp_service/          # Automated OTP handling
│   ├── profiles/             # Persistent browser profiles
│   └── frontend/             # React-based UI dashboard
├── samay-v4/                 # Desktop automation approach (PyAutoGUI)
│   ├── desktop_automation/   # Platform-specific automation
│   ├── orchestrator/         # Desktop service management
│   └── frontend/             # Enhanced React UI
├── samay-v5/                 # Hybrid API + Browser automation
│   ├── ai_automation/        # Advanced automation strategies
│   ├── backend/             # FastAPI with authentication
│   ├── core/                # API managers and response synthesis
│   └── frontend/            # Modern React dashboard
├── samay-v6/                 # Browser extension architecture (Current)
│   ├── extension/           # Chrome Manifest V3 extension
│   ├── web-app/            # React frontend + FastAPI backend
│   └── automation/         # Service-specific automation scripts
├── Samay_MacOS/             # Native macOS application experiment
│   ├── Samay_MacOS/        # SwiftUI native application
│   ├── Swift automation/   # Accessibility API integration
│   └── System integrations/ # Calendar, Mail, Weather services
├── INFORMATION/             # Project documentation & research
├── test-results/            # Testing artifacts
└── README.md               # This file
```

## 🔧 Architecture Evolution

### **Samay v3** - Browser Automation Foundation
- **Anti-bot protection** with SeleniumBase UC Mode
- **Persistent sessions** across computer restarts
- **Automated OTP fetching** via Gmail API
- **Multi-service support** (Claude, Gemini, Perplexity)
- **Status**: Production ready, stable session management

### **Samay v4** - Desktop Automation Approach
- **PyAutoGUI-based** screen automation
- **Desktop application targeting** (Claude Desktop, etc.)
- **Cross-platform automation** with macOS focus
- **Enhanced response processing** and aggregation
- **Status**: Prototype phase, platform-specific challenges

### **Samay v5** - Hybrid API + Browser Strategy
- **Dual-mode operation**: API integration + browser fallback
- **Advanced authentication** management with credential storage
- **Rate limiting** and API quota management
- **Weather & News APIs** integration for context
- **Modern FastAPI backend** with React dashboard
- **Status**: Feature-complete, API cost considerations

### **Samay v6** - Browser Extension Architecture (Current)
- **Chrome Manifest V3** extension with zero API costs
- **Bridge communication** between web app and extension
- **Service-specific automation** scripts for each AI platform
- **Real-time response extraction** and synthesis
- **Cross-origin communication** with security compliance
- **Status**: Active development, query submission phase complete

### **Samay MacOS** - Native Application Experiment
- **SwiftUI native interface** with system integration
- **Accessibility API automation** for precise control
- **System services integration** (Calendar, Mail, Weather)
- **Menu bar application** with background operation
- **Apple Events** and AppleScript automation
- **Status**: Research prototype, TCC permission challenges

### **Research & Documentation**
- **Multi-architecture analysis** and performance comparisons
- **Anti-bot detection research** across all approaches
- **Platform-specific implementation** strategies
- **Security and privacy** considerations for each architecture

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** with conda environment (v3, v4, v5)
- **Node.js 16+** for React UI (all versions)
- **Chrome browser** for automation and extension
- **Xcode** for macOS native development (Samay MacOS)

### Choose Your Version

#### **Samay v6** (Recommended - Current Development)
```bash
# Clone the repository
git clone https://github.com/akshitharsola/Samay.git
cd Samay/samay-v6

# Backend setup
cd web-app/backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python main_simple.py

# Frontend setup (new terminal)
cd web-app/frontend
npm install
npm start

# Extension setup
# 1. Open chrome://extensions/
# 2. Enable Developer mode
# 3. Load unpacked: samay-v6/extension/
```

#### **Samay v5** (Feature Complete)
```bash
cd Samay/samay-v5

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Frontend setup
cd frontend
npm install
npm start
```

#### **Samay v3** (Stable Production)
```bash
cd Samay/samay-v3
source /opt/anaconda3/bin/activate samay
pip install -r requirements.txt

# Set up the React UI
cd frontend
npm install
```

#### **Samay MacOS** (Native Experiment)
```bash
cd Samay/Samay_MacOS
# Open Samay_MacOS.xcodeproj in Xcode
# Build and run (requires macOS development setup)
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

### **Version Comparison**

| Feature | v3 | v4 | v5 | v6 | MacOS |
|---------|----|----|----|----|-------|
| **Session Management** | ✅ Production | ✅ Working | ✅ Advanced | ✅ Bridge-based | 🔄 Research |
| **Query Submission** | ✅ Stable | ✅ Working | ✅ Dual-mode | ✅ **Complete** | 🔄 Prototype |
| **Response Extraction** | ✅ Working | ✅ Enhanced | ✅ Advanced | 🔄 **In Progress** | 🔄 Basic |
| **Anti-Bot Protection** | ✅ Advanced | ⚠️ Limited | ✅ Improved | ✅ Extension-based | ✅ Native |
| **API Integration** | ❌ None | ❌ None | ✅ Full | ❌ Zero-cost | 🔄 System APIs |
| **Cross-Platform** | ✅ Yes | ⚠️ Limited | ✅ Yes | ✅ Chrome-based | ❌ macOS only |
| **Cost** | 🆓 Free | 🆓 Free | 💰 API costs | 🆓 **Zero cost** | 🆓 Free |

### **Current Focus: Samay v6**
- ✅ **Query Submission Phase** - Complete (All 4 services)
- 🔄 **Response Extraction** - Next milestone
- 🔄 **Data Synthesis** - Planned
- 🔄 **Follow-up Automation** - Future
- 🔄 **Export Features** - Future

### **Architectural Lessons Learned**
- **v3**: Proven session persistence, but maintenance intensive
- **v4**: Desktop automation limitations, platform dependencies
- **v5**: Feature-rich but API costs prohibitive
- **v6**: Zero-cost solution with extension architecture
- **MacOS**: Native integration potential, permission complexity

## 🎉 Success Metrics

When properly configured:
1. **Browser opens with persistent profiles** (not guest mode)
2. **Sessions survive computer restarts** (no re-login required)
3. **Health check shows all services active**
4. **OTP codes retrieved automatically**
5. **UI dashboard shows real-time status**

## 📝 Documentation

### **Comprehensive Documentation Available:**

- **`INFORMATION/`** - Multi-version research and implementation plans
- **`PROJECT_STATUS_REPORT_03082025.md`** - Latest v6 development status
- **Version-specific READMEs** - Individual setup and usage guides
- **Research Findings** - Anti-bot detection and automation solutions
- **Architecture Analysis** - Multi-version comparison and lessons learned

### **Latest Project Report**
See [`PROJECT_STATUS_REPORT_03082025.md`](./PROJECT_STATUS_REPORT_03082025.md) for:
- Complete v6 implementation status
- Query submission milestone achievement
- Next phase roadmap (response extraction)
- Technical architecture details
- User's modularization insights

## 🤝 Contributing

This is a research project exploring multiple AI automation architectures. Each version represents different approaches to the same challenge. Feel free to explore, learn from, and adapt any approach for your needs.

## 📄 License

MIT License - see individual component directories for specific licensing.

---

### **🚀 Quick Start by Version:**
- **Production Stability**: `cd samay-v3 && python orchestrator/manager.py`
- **Feature Rich**: `cd samay-v5 && python backend/main.py`
- **Current Development**: `cd samay-v6 && npm start` (see setup above)
- **Native macOS**: Open `Samay_MacOS/Samay_MacOS.xcodeproj` in Xcode

**Latest Achievement**: ✅ **Samay v6 successfully submits queries to all 4 AI services (Aug 2025)**

Built with ❤️ through continuous architectural evolution and experimentation