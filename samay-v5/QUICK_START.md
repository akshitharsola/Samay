# 🚀 Samay v5 - Quick Start Guide

## ⚡ **5-Minute Setup**

Since you already have the `samay` virtual environment, here's the fastest way to get Samay v5 running:

---

## 📝 **Step 1: Get Essential API Keys (5 minutes)**

### **🌤️ Weather API (Essential)**
1. Go to: https://openweathermap.org/api
2. Click "Sign Up" (free)
3. Get your API key from dashboard
4. **Copy this key** - you'll need it in Step 3

### **📰 News API (Recommended)**
1. Go to: https://newsapi.org/
2. Click "Get API Key" (free)
3. Get your API key
4. **Copy this key** - you'll need it in Step 3

---

## 🔧 **Step 2: Setup Samay v5**

```bash
cd /Users/akshitharsola/Documents/Samay/samay-v5
./setup.sh
```

The setup script will:
- ✅ Find your existing `samay` virtual environment
- ✅ Install required dependencies  
- ✅ Create configuration files
- ✅ Set up database and directories
- ✅ Create test and start scripts

---

## 🔑 **Step 3: Configure API Keys**

```bash
# Copy environment template
cp .env.example .env

# Edit the file (use your preferred editor)
nano .env
```

**Add your API keys:**
```env
# Essential (get this one for sure!)
OPENWEATHER_API_KEY=your_actual_weather_api_key_here

# Recommended (get this too if possible)
NEWS_API_KEY=your_actual_news_api_key_here

# Optional (you can add these later)
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key_here
OPENCAGE_API_KEY=your_opencage_api_key_here
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
```

**Save and exit** (Ctrl+X, then Y, then Enter in nano)

---

## 🧪 **Step 4: Test Everything**

```bash
./test_samay.py
```

You should see:
```
🧪 Testing Samay v5 Components
========================================
Testing API Manager...
✅ API Manager: 9 services configured
Testing Session Manager...  
✅ Session Manager: Created session session_xxx
Testing Local Assistant...
✅ Local Assistant: Initialized successfully
✅ Local Assistant: Query processed, stage: query_refinement

🎉 Core components test completed!
You can now start the backend with: python backend/main.py
```

---

## 🚀 **Step 5: Start Samay v5**

```bash
./start_samay.sh
```

This will start:
- 🤖 **Ollama** (for local AI assistant)
- 🚀 **FastAPI Backend** (http://localhost:8000)
- 💻 **React Frontend** (http://localhost:3000) - if Node.js available

---

## 🌐 **Step 6: Access Your AI Assistant**

### **API Documentation**
Visit: http://localhost:8000/docs

### **Test API Directly**
```bash
curl -X POST "http://localhost:8000/api/query/complete" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather like in London?", "user_id": "test"}'
```

### **Frontend Interface** (if available)
Visit: http://localhost:3000

---

## 🎯 **What You Can Do Now**

### **Weather Queries**
- "What's the weather in Tokyo?"
- "Weather forecast for New York"

### **News Queries** 
- "Latest news about AI"
- "Breaking news today"

### **General AI Queries**
- "Explain quantum computing"
- "Write a Python function to sort a list"
- "Compare React vs Vue"

### **Translation** (Free - no API key needed)
- "Translate 'Hello World' to Spanish"
- "How do you say 'Good morning' in French?"

---

## 🔧 **Troubleshooting**

### **If Ollama isn't working:**
```bash
# Install Ollama
brew install ollama  # On macOS
# or visit: https://ollama.ai

# Pull the model
ollama pull phi3:mini
```

### **If API keys aren't working:**
1. Check `.env` file has correct keys
2. No spaces around `=` sign
3. Restart backend: `python backend/main.py`

### **If virtual environment issues:**
```bash
# Activate samay manually
source ../samay/bin/activate  # Adjust path as needed
cd samay-v5
python backend/main.py
```

---

## 📊 **Next Steps**

Once you have the basic setup working:

1. **Get more API keys** from `API_KEYS_GUIDE.md`
2. **Test browser automation** with your Claude/Gemini/Perplexity accounts
3. **Explore the API** at http://localhost:8000/docs
4. **Build custom queries** using the conversation flow

---

## 🎉 **You're Ready!** 

Samay v5 is now running with:
- ✅ **Local AI Assistant** (Phi-3-Mini via Ollama)
- ✅ **Weather API** (real-time weather data)
- ✅ **News API** (breaking news and headlines)  
- ✅ **Translation API** (free, unlimited)
- ✅ **Session Management** (persistent conversations)
- ✅ **Intelligent Query Routing** (automatic service selection)
- ✅ **Response Synthesis** (combine multiple AI responses)

**Total setup time:** ~5-10 minutes  
**Monthly cost:** $0 with free tiers ✅

---

*Welcome to the future of AI automation! 🌟*