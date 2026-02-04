#!/bin/bash

# CyberLab Startup Script

echo "======================================================"
echo "  🚀 CyberLab - AI-Enhanced Hacking Lab Simulator  "
echo "======================================================"
echo ""

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check if database exists
if [ ! -f "cyberlab.db" ]; then
    echo "📦 Database not found. Initializing..."
    python3 database.py
    echo ""
fi

# Check Docker
if command -v docker &> /dev/null && docker ps &> /dev/null; then
    echo "✅ Docker is running - Full container support enabled"
else
    echo "⚠️  Docker not found or not running - Running in MOCK MODE"
    echo "   Install Docker for full container functionality"
fi
echo ""

# Check DeepSeek API key
if [ -f ".env" ] && grep -q "DEEPSEEK_API_KEY=." .env; then
    echo "✅ DeepSeek API key found - AI features enabled"
else
    echo "⚠️  No DeepSeek API key - Running AI in MOCK MODE"
    echo "   Get free API key at: https://platform.deepseek.com"
fi
echo ""

# Check if requirements are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Dependencies not installed. Installing..."
    pip3 install -r requirements.txt
    echo ""
fi

echo "======================================================"
echo "🌐 Starting CyberLab Server..."
echo "======================================================"
echo ""
echo "📍 Access the platform at: http://localhost:5000"
echo "👤 Default admin: admin / admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================================"
echo ""

# Start the application
python3 app.py