#!/bin/bash

echo "🚀 STARTING SAMAY V3 LIVE DEMO"
echo "================================"

# Function to handle cleanup
cleanup() {
    echo "🛑 Shutting down Samay v3..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "📡 Starting FastAPI Backend..."
cd "$(dirname "$0")"
python -m uvicorn web_api:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "⏳ Waiting for backend to start..."
sleep 5

echo "🎨 Starting React Frontend..."
cd frontend
npm start &
FRONTEND_PID=$!

echo "✅ SAMAY V3 IS NOW RUNNING!"
echo "🌐 Backend API: http://localhost:8000"
echo "🎨 Frontend UI: http://localhost:3000"
echo "📊 API Docs: http://localhost:8000/docs"
echo ""
echo "💡 The browser should open automatically to the frontend"
echo "🛑 Press Ctrl+C to stop both services"
echo ""

# Wait for user interrupt
wait
