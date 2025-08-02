# 🔑 Samay v5 - Complete API Keys Guide

## 📋 **Required API Keys Overview**

Samay v5 uses a combination of **free utility APIs** and **browser automation** for AI services. Here's everything you need:

---

## 🆓 **FREE Utility APIs** (Recommended to get all)

### **1. Weather API - OpenWeatherMap** ⭐ **ESSENTIAL**
- **Service**: Real-time weather data
- **Free Tier**: 1,000 calls/day
- **Cost**: FREE
- **How to Get**:
  1. Visit: https://openweathermap.org/api
  2. Sign up for free account
  3. Get your API key from dashboard
- **Environment Variable**: `OPENWEATHER_API_KEY`

### **2. News API** ⭐ **HIGHLY RECOMMENDED**
- **Service**: Breaking news and headlines
- **Free Tier**: 1,000 requests/day
- **Cost**: FREE
- **How to Get**:
  1. Visit: https://newsapi.org/
  2. Sign up for free account
  3. Get your API key
- **Environment Variable**: `NEWS_API_KEY`

### **3. Currency Exchange API** ⭐ **RECOMMENDED**
- **Service**: Real-time currency conversion
- **Free Tier**: 1,500 requests/month
- **Cost**: FREE
- **How to Get**:
  1. Visit: https://app.exchangerate-api.com/sign-up
  2. Sign up for free account
  3. Get your API key
- **Environment Variable**: `EXCHANGE_RATE_API_KEY`

### **4. Geocoding API - OpenCage** ⭐ **RECOMMENDED**
- **Service**: Location and address lookup
- **Free Tier**: 2,500 requests/day
- **Cost**: FREE
- **How to Get**:
  1. Visit: https://opencagedata.com/api
  2. Sign up for free account
  3. Get your API key
- **Environment Variable**: `OPENCAGE_API_KEY`

### **5. Stock Data API - Alpha Vantage** 💰 **OPTIONAL**
- **Service**: Stock prices and financial data
- **Free Tier**: 5 calls/minute, 500 calls/day
- **Cost**: FREE
- **How to Get**:
  1. Visit: https://www.alphavantage.co/support/#api-key
  2. Get free API key (no signup required)
- **Environment Variable**: `ALPHA_VANTAGE_API_KEY`

### **6. Translation API - MyMemory** ✅ **FREE (No Key Required)**
- **Service**: Text translation
- **Free Tier**: Unlimited
- **Cost**: FREE
- **No API Key Needed**: Uses public endpoint

---

## 🤖 **AI Services** (Browser Automation - No API Keys Required)

### **Claude, Gemini, Perplexity**
- **Method**: Browser automation with your existing accounts
- **Cost**: Uses your existing subscriptions (Pro/Advanced recommended)
- **Setup**: 
  - Make sure you have accounts on:
    - Claude.ai (Claude Pro recommended)
    - Gemini.google.com (Gemini Advanced recommended)
    - Perplexity.ai (Perplexity Pro recommended)
  - Samay will use browser automation to access these services
  - **No API keys required** - uses your logged-in browser sessions

---

## ⚙️ **Environment Configuration**

### **1. Copy Environment Template**
```bash
cp .env.example .env
```

### **2. Edit .env File**
```bash
nano .env
```

### **3. Add Your API Keys**
```env
# Core Application Settings
ENVIRONMENT=development
DEBUG=true
HOST=localhost
PORT=8000

# Database
DATABASE_URL=sqlite:///./storage/samay.db

# 🔑 REQUIRED API KEYS (Get these for full functionality)
OPENWEATHER_API_KEY=your_openweather_api_key_here
NEWS_API_KEY=your_news_api_key_here
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key_here
OPENCAGE_API_KEY=your_opencage_api_key_here

# 🔑 OPTIONAL API KEYS
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Local LLM Configuration (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
LOCAL_MODEL=phi3:mini

# Browser Automation Settings
CHROME_PROFILE_PATH=./profiles
HEADLESS=false
AUTOMATION_DELAY=1.5

# Security (auto-generated during setup)
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# CORS Settings
ALLOWED_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/samay.log

# Rate Limiting
RATE_LIMIT_ENABLED=true
DEFAULT_RATE_LIMIT=100/minute
```

---

## 🚀 **Quick Setup Instructions**

### **Step 1: Get Essential API Keys (5 minutes)**
1. **OpenWeatherMap** (Essential): https://openweathermap.org/api
2. **NewsAPI** (Recommended): https://newsapi.org/
3. **ExchangeRate-API** (Recommended): https://app.exchangerate-api.com/sign-up
4. **OpenCage** (Recommended): https://opencagedata.com/api

### **Step 2: Configure Environment**
```bash
cd samay-v5
cp .env.example .env
nano .env  # Add your API keys
```

### **Step 3: Run Setup**
```bash
./setup.sh
```

---

## 💰 **Cost Breakdown**

### **FREE TIER USAGE**
- **Weather**: 1,000 calls/day = ~30,000/month
- **News**: 1,000 calls/day = ~30,000/month  
- **Currency**: 1,500 calls/month
- **Geocoding**: 2,500 calls/day = ~75,000/month
- **Stock**: 500 calls/day = ~15,000/month
- **Translation**: Unlimited
- **AI Services**: Use your existing subscriptions

### **ESTIMATED MONTHLY COSTS**
- **Light Usage** (< 100 queries/day): **$0/month** ✅
- **Medium Usage** (< 500 queries/day): **$0/month** ✅
- **Heavy Usage** (> 1000 queries/day): **$0-5/month** 💰

---

## 🔧 **Advanced Configuration**

### **Custom API Endpoints**
You can customize API endpoints in `config/api_services.yaml`:

```yaml
utility_apis:
  weather:
    provider: "openweathermap"
    api_key_env: "OPENWEATHER_API_KEY"
    endpoints:
      current: "https://api.openweathermap.org/data/2.5/weather"
      forecast: "https://api.openweathermap.org/data/2.5/forecast"
```

### **Rate Limit Configuration**
Adjust rate limits in `config/rate_limits.yaml`:

```yaml
rate_limits:
  utility_apis:
    weather:
      requests_per_day: 1000
      requests_per_minute: 60
```

---

## 🧪 **Testing API Keys**

### **Test Individual APIs**
```bash
# Activate samay environment
source ../samay/bin/activate  # Or wherever your samay venv is

# Test weather API
python -c "
import os
import requests
api_key = os.getenv('OPENWEATHER_API_KEY')
if api_key:
    r = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}')
    print('Weather API:', 'OK' if r.status_code == 200 else 'Failed')
else:
    print('Weather API key not set')
"
```

### **Test All APIs at Once**
```bash
./test_samay.py
```

---

## ❓ **Troubleshooting**

### **Common Issues**

#### **"API key not configured" errors**
- Check that your `.env` file has the correct API keys
- Ensure no extra spaces around the `=` sign
- Restart the backend after changing `.env`

#### **"Service unavailable" errors**
- Check your internet connection
- Verify API keys are valid and not expired
- Check if you've exceeded free tier limits

#### **Browser automation issues**
- Make sure you're logged into Claude, Gemini, Perplexity in your default browser
- Check that Chrome is installed and updated
- Ollama should be running for local assistant features

### **Getting Help**
1. Check the logs: `tail -f logs/samay.log`
2. Test components: `./test_samay.py`
3. Check service status: Visit `http://localhost:8000/api/services/status`

---

## 📚 **API Documentation Links**

- **OpenWeatherMap**: https://openweathermap.org/api
- **NewsAPI**: https://newsapi.org/docs
- **ExchangeRate-API**: https://app.exchangerate-api.com/documentation
- **OpenCage**: https://opencagedata.com/api
- **Alpha Vantage**: https://www.alphavantage.co/documentation/

---

## ✅ **Ready to Go!**

Once you have your API keys configured:

1. **Essential APIs**: OpenWeatherMap, NewsAPI ⚡
2. **Recommended APIs**: ExchangeRate, OpenCage 🌟  
3. **Optional APIs**: Alpha Vantage 💰
4. **AI Services**: Your existing Claude/Gemini/Perplexity accounts 🤖

**Total Setup Time**: ~5-10 minutes  
**Total Cost**: $0/month for most users ✅

---

*Happy automating with Samay v5! 🚀*