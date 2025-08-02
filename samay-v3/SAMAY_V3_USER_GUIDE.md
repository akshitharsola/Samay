# 🤖 Samay v3 - Intelligent Companion Platform User Guide

## 📋 Table of Contents
- [Quick Start](#quick-start)
- [System Requirements](#system-requirements)
- [Installation & Setup](#installation--setup)
- [Starting the Assistant](#starting-the-assistant)
- [How to Use Samay v3](#how-to-use-samay-v3)
- [Service Modes](#service-modes)
- [Features Overview](#features-overview)
- [Troubleshooting](#troubleshooting)
- [Stopping the Assistant](#stopping-the-assistant)
- [Advanced Configuration](#advanced-configuration)

---

## 🚀 Quick Start

### **Start Samay v3 in 3 Steps:**

```bash
# 1. Start the backend API
python -m uvicorn web_api:app --reload --port 8000

# 2. Start the frontend UI (in another terminal)
cd frontend && npm start

# 3. Open your browser
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

## 💻 System Requirements

### **Required Software:**
- **Python 3.8+** (preferably 3.11 or higher)
- **Node.js 16+** and **npm**
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

### **Optional Dependencies:**
- **Ollama** (for local LLM integration with Phi-3-Mini)
- **Chrome/Chromium** (for web services automation)

### **System Resources:**
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB for dependencies and databases
- **Network**: Internet connection for web services mode

---

## 🔧 Installation & Setup

### **1. Install Python Dependencies**
```bash
# Navigate to project directory
cd /path/to/samay-v3

# Install required packages
pip install fastapi uvicorn websockets seleniumbase requests ollama aiofiles
```

### **2. Setup Frontend**
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

### **3. Optional: Install Ollama for Local LLM**
```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Download Phi-3-Mini model
ollama pull phi3:mini
```

---

## 🎯 Starting the Assistant

### **Method 1: Manual Start (Recommended)**

**Terminal 1 - Backend:**
```bash
cd /path/to/samay-v3
python -m uvicorn web_api:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd /path/to/samay-v3/frontend
npm start
```

### **Method 2: Using Startup Script**
```bash
# Make script executable
chmod +x start_samay_live.sh

# Run startup script
./start_samay_live.sh
```

### **Method 3: Development Mode**
```bash
# Backend with auto-reload
python -m uvicorn web_api:app --reload --port 8000

# Frontend with hot-reload
cd frontend && npm run dev
```

### **✅ Verification**
After starting, you should see:
- **Backend**: Server running at `http://localhost:8000`
- **Frontend**: React app at `http://localhost:3000`
- **Browser**: Automatically opens to the frontend

---

## 🎭 How to Use Samay v3

### **Main Interface Overview**

When you open `http://localhost:3000`, you'll see **6 main tabs**:

#### **1. 📊 Smart Dashboard**
- **Real-time productivity metrics**
- **Today's AI-optimized schedule**
- **Proactive suggestions panel**
- **Quick action buttons**

```
Usage: View your daily overview and productivity insights
```

#### **2. 💬 Enhanced Chat**
- **Main conversation interface**
- **Persistent memory across sessions**
- **Adaptive personality learning**
- **Contextual suggestions sidebar**

```
Usage: Chat with your AI companion
Example: "Help me plan my day" or "What should I work on next?"
```

#### **3. 🌐 Web Services Panel**
- **Multi-service queries** (Claude, Gemini, Perplexity)
- **Output format selection** (JSON, Text, Markdown)
- **Parallel processing status**
- **Response quality metrics**

```
Usage: Get comprehensive answers from multiple AI services
Example: "Latest AI development trends" with all services enabled
```

#### **4. ⚙️ Workflow Builder**
- **Visual workflow creation**
- **Pre-built automation templates**
- **Real-time execution monitoring**
- **Custom trigger configuration**

```
Usage: Automate repetitive tasks
Example: Create "Daily Standup Preparation" workflow
```

#### **5. 📚 Knowledge Panel**
- **Intelligent content management**
- **Multi-modal search** (Semantic, Exact, Fuzzy)
- **AI-generated insights**
- **Relationship mapping**

```
Usage: Store and search your knowledge base
Example: Add project documentation and search for insights
```

#### **6. 💬 Legacy Chat**
- **Original multi-agent interface**
- **Simple query-response format**
- **Service comparison mode**

```
Usage: Basic AI interactions for comparison
```

---

## 🔄 Service Modes

Samay v3 offers **4 processing modes** you can select:

### **🔒 Local Only Mode**
- **Privacy**: Maximum (all processing local)
- **Speed**: Fast (2-3 seconds)
- **Cost**: Free
- **Accuracy**: Good (85%)
- **Use Case**: Sensitive data, offline work

```bash
How to use: Select "Local Only" in Enhanced Chat
Best for: Private conversations, offline scenarios
```

### **🛡️ Confidential Mode**
- **Privacy**: Enterprise-grade
- **Speed**: Fast (3-4 seconds)
- **Cost**: Free
- **Accuracy**: Very Good (90%)
- **Use Case**: Business/healthcare data

```bash
How to use: Enable "Confidential Mode" in Web Services Panel
Best for: GDPR/HIPAA compliant processing
```

### **🌐 Web Services Mode**
- **Privacy**: Standard
- **Speed**: Medium (5-8 seconds)
- **Cost**: API costs apply
- **Accuracy**: Excellent (95%)
- **Use Case**: Latest information, high accuracy

```bash
How to use: Select services in Web Services Panel
Best for: Research, current events, complex analysis
```

### **🎛️ Hybrid Mode**
- **Privacy**: Configurable
- **Speed**: Medium (6-10 seconds)
- **Cost**: Moderate
- **Accuracy**: Optimal (97%)
- **Use Case**: Best overall experience

```bash
How to use: Default mode combining all capabilities
Best for: General daily assistance
```

---

## 🌟 Features Overview

### **Core Capabilities**

#### **💭 Intelligent Conversation**
```
• Persistent memory across sessions
• Adaptive personality learning
• Context-aware responses
• Natural language understanding
```

#### **🧠 Advanced Brainstorming**
```
• Multi-round iterative refinement
• Quality assessment and scoring
• Version control for ideas
• Alternative approach exploration
```

#### **📅 Smart Task Management**
```
• AI-optimized scheduling
• Energy-based task allocation
• Natural language task creation
• Productivity analytics
```

#### **🤖 Proactive Assistance**
```
• Context-aware suggestions
• Behavioral pattern recognition
• Automatic workflow triggers
• Wellness monitoring
```

#### **📊 Comprehensive Analytics**
```
• Real-time productivity metrics
• 7-day trend analysis
• Performance optimization
• Usage insights
```

### **Example Interactions**

#### **Basic Conversation:**
```
You: "Hello! I'm working on a presentation about AI."
Samay: "Hi! I'd be happy to help with your AI presentation. I can assist with content structure, current trends, or specific technical topics. What aspect would you like to focus on first?"
```

#### **Task Creation:**
```
You: "Remind me to review the presentation tomorrow at 2 PM"
Samay: "Task created: 'Review AI presentation'
• Priority: Medium
• Scheduled: Tomorrow 2:00 PM
• Duration: 30 minutes estimated
Added to your smart schedule."
```

#### **Proactive Suggestion:**
```
Samay: "I notice you've been working on your presentation for 90 minutes. Consider taking a 10-minute break to maintain focus. Would you like me to schedule a break reminder?"
```

---

## 🛠️ Troubleshooting

### **Common Issues**

#### **Backend Won't Start**
```bash
Error: "Module not found: fastapi"
Solution: pip install fastapi uvicorn
```

#### **Frontend Shows Error**
```bash
Error: "npm command not found"
Solution: Install Node.js from nodejs.org
```

#### **Port Already in Use**
```bash
Error: "Port 8000 already in use"
Solution: 
- Kill existing process: lsof -ti:8000 | xargs kill -9
- Or use different port: --port 8001
```

#### **Local LLM Not Working**
```bash
Error: "Ollama connection failed"
Solution:
1. Install Ollama: brew install ollama
2. Start service: ollama serve
3. Download model: ollama pull phi3:mini
```

#### **Web Services Not Responding**
```bash
Error: "Service timeout"
Solution:
1. Check internet connection
2. Verify service credentials
3. Use Local Only mode as fallback
```

### **Performance Issues**

#### **Slow Response Times**
```bash
Possible causes:
• Large database files - optimize or clean
• Multiple concurrent users - increase resources
• Network latency - check connection

Solutions:
• Restart services
• Clear browser cache
• Use Local Only mode
```

#### **High Memory Usage**
```bash
Monitoring: Check with top or Activity Monitor
Solutions:
• Restart every few hours
• Limit concurrent sessions
• Close unused browser tabs
```

---

## 🛑 Stopping the Assistant

### **Method 1: Graceful Shutdown**
```bash
# In each terminal running services:
Ctrl + C

# Or if using startup script:
Ctrl + C (will stop both services)
```

### **Method 2: Kill Processes**
```bash
# Find and kill backend
lsof -ti:8000 | xargs kill -9

# Find and kill frontend
lsof -ti:3000 | xargs kill -9
```

### **Method 3: System Restart**
```bash
# Nuclear option - restart your computer
sudo reboot
```

### **✅ Verification**
Confirm shutdown by checking:
- Browser: `http://localhost:3000` shows connection error
- API: `http://localhost:8000` shows connection error
- Processes: No Python/Node processes related to Samay

---

## ⚙️ Advanced Configuration

### **Environment Variables**
Create `.env` file in project root:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG_MODE=true

# LLM Configuration
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=phi3:mini

# Database Configuration
DATABASE_PATH=./memory/
MAX_CONNECTIONS=100

# Web Services (optional)
CLAUDE_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
PERPLEXITY_API_KEY=your_key_here
```

### **Service Configuration**
Edit `web_api.py` for advanced settings:
```python
# Response timeouts
RESPONSE_TIMEOUT = 30

# Maximum concurrent sessions
MAX_SESSIONS = 50

# Memory retention period
MEMORY_RETENTION_DAYS = 30
```

### **Frontend Customization**
Edit `frontend/src/config.js`:
```javascript
export const CONFIG = {
  API_BASE_URL: 'http://localhost:8000',
  WEBSOCKET_URL: 'ws://localhost:8000/ws',
  AUTO_REFRESH_INTERVAL: 30000, // 30 seconds
  MAX_MESSAGE_LENGTH: 5000
};
```

---

## 📊 Monitoring & Maintenance

### **Health Checks**
```bash
# API health
curl http://localhost:8000/health

# Database status
ls -la memory/*.db

# Log files
tail -f logs/samay.log
```

### **Regular Maintenance**
```bash
# Weekly database cleanup
python maintenance/cleanup_old_data.py

# Monthly backup
cp -r memory/ backups/memory_$(date +%Y%m%d)/

# Update dependencies
pip install --upgrade -r requirements.txt
cd frontend && npm update
```

---

## 🔐 Security Best Practices

### **Data Protection**
- **Local Mode**: Use for sensitive data
- **Confidential Mode**: GDPR/HIPAA compliance
- **Regular Backups**: Protect conversation history
- **Access Control**: Limit network access if needed

### **Network Security**
```bash
# Restrict to localhost only
--host 127.0.0.1

# Use HTTPS in production
--ssl-keyfile key.pem --ssl-certfile cert.pem
```

---

## 📞 Support & Resources

### **Documentation**
- **API Docs**: http://localhost:8000/docs (when running)
- **Phase Summaries**: `PHASE*_SUMMARY.md` files
- **Testing Guide**: `MANUAL_TESTING_GUIDE.md`

### **Getting Help**
1. **Check logs** in `logs/` directory
2. **Review error messages** in browser console
3. **Test with minimal configuration**
4. **Use Local Only mode** as fallback

### **Community & Updates**
- **Project Repository**: Check for updates
- **Issue Tracking**: Report bugs or feature requests
- **Version History**: See `FINAL_PROJECT_COMPLETION_SUMMARY.md`

---

## 🎉 Enjoy Your AI Companion!

Samay v3 is your **intelligent companion** designed to enhance productivity, provide comprehensive assistance, and adapt to your unique working style. 

**Start exploring** with simple conversations and gradually discover the advanced features like workflow automation, knowledge management, and multi-service processing.

**Welcome to the future of AI assistance!** 🌟

---

*Last updated: July 26, 2025*  
*Version: Samay v3 Production Release*