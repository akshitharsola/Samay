# 🚀 Samay v5 - Next-Generation API-First AI Assistant

## Overview
Samay v5 is a production-ready, API-first multi-agent AI assistant that provides intelligent conversation flow and service orchestration.

## Key Features
- **API-First Architecture**: Direct integration with Claude, Gemini, Perplexity APIs
- **Local Assistant Integration**: Built-in conversation with Phi-3-Mini before routing to services
- **Persistent Session Management**: No repetitive logins, saved authentication
- **Professional User Experience**: Modern interface with intelligent workflow
- **Production Deployment Ready**: Scalable, maintainable, and reliable

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional)

### Installation
```bash
git clone [repository-url]
cd samay-v5
chmod +x setup.sh
./setup.sh
```

### Configuration
1. Copy `.env.example` to `.env`
2. Add your API keys for various services
3. Configure service settings in `config/` directory

### Running the Application
```bash
# Start backend
python backend/main.py

# Start frontend (in another terminal)
cd frontend && npm start
```

## Architecture
- **Backend**: FastAPI with async support
- **Frontend**: React 18 with TypeScript
- **Local LLM**: Ollama with Phi-3-Mini
- **Database**: SQLite for development, PostgreSQL for production
- **Deployment**: Docker, Kubernetes ready

## API Services
- Claude (Anthropic)
- Gemini (Google)
- Perplexity AI
- Various utility APIs (weather, news, etc.)

## Documentation
See the `docs/` directory for detailed documentation.

---
Built with ❤️ for seamless AI automation