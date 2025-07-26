# Samay v3 - Multi-Agent AI Session Manager

🚀 **Research-based solution for persistent, anti-bot resistant AI sessions using Ollama**

> **Note**: This project uses Ollama models for local AI processing. **Ollama model files cannot be uploaded to this repository due to size constraints** (typically 4-7GB per model). Models must be installed separately via Ollama CLI.

## 🎯 What This Solves

- **❌ Repeated manual logins** → ✅ **Persistent sessions across restarts**
- **❌ Guest mode browsers** → ✅ **Real Chrome profiles with UC Mode stealth**
- **❌ Anti-bot detection loops** → ✅ **SeleniumBase UC Mode bypass**
- **❌ Manual OTP entry** → ✅ **Automated Gmail OTP fetching**

## 🏗️ Architecture

Based on the **Comprehensive Implementation Plan**, Samay v3 uses:

| Component | Purpose | Technology |
|-----------|---------|------------|
| **UC Profiles** | Persistent browser data | SeleniumBase UC Mode + dedicated directories |
| **Session Validation** | Detect expired logins | DOM probes + redirect detection |
| **OTP Automation** | Auto-retrieve codes | Gmail API + pattern matching |
| **Driver Factory** | Anti-bot browser creation | UC Mode with profile isolation |

## 📁 Project Structure

```
samay-v3/
├── orchestrator/
│   ├── drivers.py      # UC Mode driver factory with profiles
│   ├── validators.py   # Session authentication detection
│   └── manager.py      # Main orchestrator (run this!)
├── otp_service/
│   ├── gmail_fetcher.py    # Automated OTP retrieval
│   └── secrets/            # Gmail API credentials
├── profiles/               # Persistent Chrome profiles
│   ├── claude/            # Claude's UC profile
│   ├── gemini/            # Gemini's UC profile  
│   └── perplexity/        # Perplexity's UC profile
├── .env                   # Configuration
└── requirements.txt       # Dependencies
```

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to samay-v3
cd /Users/akshitharsola/Documents/Samay/samay-v3

# Activate your conda environment
source /opt/anaconda3/bin/activate samay

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Update `.env` with your details:

```bash
# Your email for OTP codes
CLAUDE_EMAIL=your-email@gmail.com
GOOGLE_USER=your-email@gmail.com

# Optional: Proxy settings
CLAUDE_PROXY=
GEMINI_PROXY=
PERPLEXITY_PROXY=
```

### 3. Gmail API Setup (for OTP automation)

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create project → Enable Gmail API
3. Create credentials (Desktop application)
4. Download `credentials.json`
5. Place at `otp_service/secrets/credentials.json`

### 4. Run Setup

```bash
# Run the main manager
python orchestrator/manager.py

# Choose option 1: Setup wizard
# Follow prompts to initialize each service
```

## 🎛️ Usage

### First Time Setup

```bash
python orchestrator/manager.py
# → Option 1: Setup wizard
# → Complete manual login for each service (one-time only)
# → UC Mode handles anti-bot detection
# → Sessions are saved to persistent profiles
```

### Daily Usage

```bash
python orchestrator/manager.py  
# → Option 2: Health check
# → All services should show "authenticated"
# → No manual login required!
```

### Individual Component Testing

```bash
# Test driver factory
python orchestrator/drivers.py

# Test session validation
python orchestrator/validators.py

# Test OTP fetching
python otp_service/gmail_fetcher.py
```

## 🔧 How It Works

### Phase 1: Profile Creation
- UC Mode creates stealth-compliant Chrome profiles
- Each service gets isolated profile directory
- Manual login saved to persistent storage

### Phase 2: Session Validation
- Automatic detection of expired sessions
- DOM element probing + URL redirect checks  
- Service-specific authentication verification

### Phase 3: Auto-Recovery
- Gmail API fetches OTP codes automatically
- Intelligent pattern matching for different code formats
- Seamless re-authentication when needed

## 🛡️ Key Features

### ✅ Anti-Bot Protection
- **SeleniumBase UC Mode**: Advanced fingerprint spoofing
- **Human-like behavior**: Random delays, realistic interactions
- **Residential proxy support**: IP rotation per service

### ✅ Session Persistence  
- **UC-generated profiles**: Only profiles created by UC Mode work
- **Lock file cleanup**: Prevents "profile in use" errors
- **Cross-restart durability**: Sessions survive computer reboots

### ✅ OTP Automation
- **Gmail API integration**: Real-time email monitoring
- **Pattern recognition**: Supports 4, 6, 8 digit codes
- **Service context**: Matches codes to specific services

### ✅ Multi-Service Support
- **Claude**: Email OTP authentication
- **Gemini**: Google SSO integration  
- **Perplexity**: Standard login flow
- **Extensible**: Easy to add new services

## 🔍 Troubleshooting

### Profile Issues
```bash
# If browser opens as guest:
python orchestrator/drivers.py
# → Option 1: Initialize new profile
# → Ensure manual login completes successfully

# Clear corrupted profiles:
python orchestrator/manager.py  
# → Option 5: Reset service
```

### Authentication Issues
```bash
# Test individual service:
python orchestrator/validators.py
# → Check authentication status
# → Force login flow if needed
```

### OTP Issues
```bash
# Test Gmail API:
python otp_service/gmail_fetcher.py
# → Option 1: Test connection
# → Verify credentials.json exists
```

## 📊 Status Monitoring

### Health Check Command
```bash
python orchestrator/manager.py
# → Option 2: Health check all services
# → Shows: authenticated/needs_login/error for each service
```

### Expected Output (Success)
```
📊 Health Check Summary:
✅ Claude: Session active  
✅ Gemini: Session active
✅ Perplexity: Session active
```

## 🎉 Success Criteria

When working correctly:

1. **✅ Browser opens with real profile** (not guest mode)
2. **✅ Login persists across restarts** (no repeated authentication)  
3. **✅ Health check shows all authenticated** (sessions working)
4. **✅ OTP codes retrieved automatically** (Gmail integration)

## 🔮 Next Steps

Once basic session persistence is working:

1. **Multi-Agent Orchestration**: Send prompts to all services simultaneously
2. **Response Aggregation**: Compare and combine AI responses  
3. **Quality Validation**: Automated response completeness checking
4. **Production Scaling**: Redis queues, Docker deployment

---

## 📝 Implementation Notes

This implementation follows the **Comprehensive Implementation Plan** which identified that:

- ✅ **SeleniumBase UC Mode forces incognito** but creates real profiles
- ✅ **Path B approach** (UC-generated profiles) is the working solution  
- ✅ **OTP automation** eliminates the last manual step
- ✅ **Session validation** prevents silent logout failures

The key insight was that UC Mode creates profiles but still appears incognito-like - however, the profile data **is** persisted and **can** be reused across sessions.

**Start here**: `python orchestrator/manager.py` 🚀