# Samay v6 Complete Testing Guide
*Generated: August 2, 2025*

## 🧪 Step-by-Step Testing Instructions

Follow these steps **exactly** to test Samay v6 end-to-end functionality.

---

## 📋 Prerequisites

### Required Software
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Google Chrome** browser
- **Ollama** (optional for full LLM features)

### Check Prerequisites
```bash
# Check Python version
python3 --version

# Check Node.js version
node --version

# Check npm version
npm --version

# Check Chrome installation
which google-chrome || which "Google Chrome" || echo "Install Google Chrome"
```

---

## 🚀 Phase 1: Backend Testing

### Step 1: Navigate to Backend Directory
```bash
cd /Users/akshitharsola/Documents/Samay/samay-v6/web-app/backend
```

### Step 2: Install Python Dependencies
```bash
# Install required packages
pip3 install fastapi uvicorn websockets pydantic

# Optional: Install Ollama for full LLM features
# pip3 install ollama
```

### Step 3: Test Basic Server (Simplified Mode)
```bash
# Start the simplified server (no Ollama required)
python3 main_simple.py
```

**Expected Output:**
```
🚀 Starting Samay v6 Backend (Simplified) on 0.0.0.0:8000
📚 API Documentation: http://0.0.0.0:8000/docs
🔄 Auto-reload: False
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
🚀 Starting Samay v6 Backend (Simplified)...
✅ Basic components initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 4: Test Health Endpoints
**In a new terminal**, test the health endpoints:

```bash
# Test root endpoint
curl http://localhost:8000/

# Test health endpoint
curl http://localhost:8000/health

# Test API documentation (open in browser)
open http://localhost:8000/docs
```

**Expected Responses:**
- Root: JSON with service info and status "running"
- Health: JSON with "status": "healthy" and component statuses
- Docs: Interactive FastAPI documentation page

### Step 5: Test WebSocket Connection
```bash
# Install wscat for WebSocket testing
npm install -g wscat

# Test WebSocket connection
wscat -c ws://localhost:8000/ws/test-session-123
```

**Expected WebSocket Response:**
```json
{
  "type": "connection_established",
  "session_id": "test-session-123",
  "timestamp": "2025-08-02T...",
  "mode": "simplified"
}
```

**✅ Backend Test Complete** - Keep server running for frontend testing.

---

## 🎨 Phase 2: Frontend Testing

### Step 1: Navigate to Frontend Directory
**In a new terminal:**
```bash
cd /Users/akshitharsola/Documents/Samay/samay-v6/web-app/frontend
```

### Step 2: Install Node.js Dependencies
```bash
# Install all frontend dependencies
npm install
```

### Step 3: Start Frontend Development Server
```bash
# Start React development server
npm start
```

**Expected Output:**
```
Local:            http://localhost:3000
On Your Network:  http://192.168.x.x:3000
```

### Step 4: Test Frontend Application
1. **Open Browser**: Navigate to `http://localhost:3000`
2. **Check Status Indicators**: All three status lights should show:
   - Backend: 🟢 Healthy
   - Extension: 🔴 Not Found (expected)
   - WebSocket: 🟢 Connected

3. **Test Query Interface**: 
   - Enter test query: "What is artificial intelligence?"
   - Click "Start Automation"
   - Should see WebSocket communication in browser console

**✅ Frontend Test Complete** - Keep both servers running for extension testing.

---

## 🔧 Phase 3: Browser Extension Testing

### Step 1: Generate Extension Icons
```bash
# Open icon generator in browser
open /Users/akshitharsola/Documents/Samay/samay-v6/extension/assets/generate_icons.html
```

1. Right-click each icon and save as:
   - `icon16.png`
   - `icon32.png` 
   - `icon48.png`
   - `icon128.png`
2. Save all files to: `/Users/akshitharsola/Documents/Samay/samay-v6/extension/assets/icons/`

### Step 2: Install Extension in Chrome
1. **Open Chrome Extensions**: Navigate to `chrome://extensions/`
2. **Enable Developer Mode**: Toggle switch in top-right corner
3. **Load Extension**:
   - Click "Load unpacked"
   - Select folder: `/Users/akshitharsola/Documents/Samay/samay-v6/extension/`
   - Click "Select Folder"

### Step 3: Verify Extension Installation
1. **Check Extensions List**: Look for "Samay v6 - Multi-AI Automation"
2. **Check Browser Toolbar**: Look for Samay v6 icon
3. **Click Extension Icon**: Should open popup with status indicators

### Step 4: Test Extension Communication
1. **With Frontend and Backend Running**:
   - Click Samay v6 extension icon
   - Check popup status indicators:
     - Extension: 🟢 Active
     - Web App: 🟢 Connected (if frontend tab is open)
     - Automation: 🔴 Idle

2. **Test "Open Web App" Button**:
   - Click "Open Web App" in popup
   - Should open/focus `http://localhost:3000`

3. **Test Connection Check**:
   - Click "Check Connection" in popup
   - All indicators should update

**✅ Extension Test Complete**

---

## 🔗 Phase 4: End-to-End Integration Testing

### Prerequisites
- Backend server running (`python3 main_simple.py`)
- Frontend server running (`npm start`)
- Extension installed and active in Chrome

### Test Complete Workflow

1. **Open Web App**: Navigate to `http://localhost:3000`

2. **Verify All Connections**:
   - Backend Status: 🟢 Healthy
   - Extension Status: 🟢 Connected
   - WebSocket Status: 🟢 Connected

3. **Test Query Submission**:
   ```
   Query: "Explain quantum computing in simple terms"
   Options: Leave default
   Click: "Start Automation"
   ```

4. **Expected Behavior**:
   - Status changes to "Processing..."
   - WebSocket messages appear in browser console
   - Extension popup shows automation as "Running"
   - Automation eventually completes with placeholder responses

### Test Extension Popup During Automation

1. **During Active Automation**:
   - Click extension icon
   - Should show:
     - Extension: 🟢 Active
     - Web App: 🟢 Connected  
     - Automation: 🔵 Running
   - "Current Session" section should be visible
   - Service cards should show different states

2. **Test Stop Automation**:
   - Click "Stop Automation" in popup
   - Automation should halt
   - Status should return to idle

**✅ End-to-End Test Complete**

---

## 🐛 Troubleshooting

### Backend Issues

**"Module not found" errors:**
```bash
pip3 install fastapi uvicorn websockets pydantic
```

**Port already in use:**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

**Permission errors:**
```bash
# Use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

**"npm not found":**
- Install Node.js from https://nodejs.org/

**Port 3000 in use:**
```bash
# Find and kill process using port 3000
lsof -ti:3000 | xargs kill -9
```

**Package installation fails:**
```bash
# Clear npm cache
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Extension Issues

**Extension not loading:**
- Check Chrome version is 88+
- Ensure Developer Mode is enabled
- Try refreshing extension page

**Popup not showing:**
- Check extension permissions
- Look for errors in Chrome DevTools
- Verify all files are present

**Communication failing:**
- Check browser console for errors
- Verify both servers are running
- Test WebSocket connection manually

---

## 📊 Success Criteria

### ✅ All Tests Pass When:

1. **Backend Health Check**: Returns `"status": "healthy"`
2. **Frontend Loads**: Shows query interface with status indicators
3. **Extension Installs**: Appears in Chrome extensions list
4. **WebSocket Connects**: Real-time communication working
5. **Extension Communication**: Popup shows all services connected
6. **Query Processing**: Can submit queries and receive responses
7. **Status Updates**: Real-time status changes during automation

### 📈 Performance Expectations

- **Backend Startup**: < 5 seconds
- **Frontend Load**: < 10 seconds  
- **Extension Install**: < 30 seconds
- **WebSocket Connection**: < 2 seconds
- **Query Processing**: < 60 seconds (in simplified mode)

---

## 🎯 Next Steps After Testing

Once all tests pass, the system is ready for **Phase 2: Service Integration**:

1. **Service-specific automation scripts** for ChatGPT, Claude, Gemini, Perplexity
2. **Response extraction and monitoring** functionality
3. **Advanced error handling** and fallback mechanisms
4. **Performance optimization** and rate limiting
5. **Enhanced UI features** and user experience improvements

---

## 📞 Support

If you encounter issues during testing:

1. **Check browser console** for JavaScript errors
2. **Check terminal output** for server errors  
3. **Verify all dependencies** are installed
4. **Ensure ports 3000 and 8000** are available
5. **Try restarting** all services in order: Backend → Frontend → Extension

**Testing Complete**: Your Samay v6 foundation is ready for Phase 2 development! 🚀