#!/bin/bash

# Hoopie Streaming Agent Setup Script
# Sets up the environment and dependencies for WebSocket streaming

set -e  # Exit on any error

echo "🚀 Setting up Hoopie Streaming Agent..."

# Check if we're in the right directory
if [ ! -f "streaming_agent.py" ]; then
    echo "❌ Error: streaming_agent.py not found. Please run this script from backend/end-points/"
    exit 1
fi

# Check for uv package manager (preferred)
if command -v uv &> /dev/null; then
    echo "✅ Using uv package manager"
    PYTHON_CMD="uv run python"
    INSTALL_CMD="uv add"

    # Initialize uv project if needed
    if [ ! -f "pyproject.toml" ]; then
        echo "📦 Initializing uv project..."
        uv init --no-readme
    fi

    # Install dependencies
    echo "📦 Installing dependencies with uv..."
    uv add fastapi uvicorn[standard] websockets google-adk google-generativeai google-cloud-aiplatform python-dotenv numpy

elif command -v pip &> /dev/null; then
    echo "✅ Using pip package manager"
    PYTHON_CMD="python"
    INSTALL_CMD="pip install"

    # Install dependencies
    echo "📦 Installing dependencies with pip..."
    pip install -r requirements.txt

else
    echo "❌ Error: Neither uv nor pip found. Please install Python package manager."
    exit 1
fi

# Setup environment file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Set region to us-central1 for streaming support
echo "🌍 Configuring for us-central1 region (required for streaming models)..."

# Export environment variables for this session
export GOOGLE_GENAI_USE_VERTEXAI=TRUE
export GOOGLE_CLOUD_PROJECT=hoopie-dev
export GOOGLE_CLOUD_LOCATION=us-central1

echo "✅ Environment configured for streaming"

# Check if port 8000 is available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8000 is already in use. Stopping existing processes..."
    sudo lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

echo "🎯 Testing streaming agent setup..."

# Test import
$PYTHON_CMD -c "
try:
    import sys, os
    sys.path.append('../../hoopie-adk')
    from hoopie_sdm.agent import root_agent
    from google.adk.runners import InMemoryRunner
    from fastapi import FastAPI
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Setup completed successfully!"
    echo ""
    echo "🚀 To start the streaming agent:"
    echo "   cd backend/end-points"
    echo "   export GOOGLE_GENAI_USE_VERTEXAI=TRUE"
    echo "   export GOOGLE_CLOUD_PROJECT=hoopie-dev"
    echo "   export GOOGLE_CLOUD_LOCATION=us-central1"
    echo "   $PYTHON_CMD -m uvicorn streaming_agent:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
    echo "🧪 To test the setup:"
    echo "   $PYTHON_CMD test_streaming_client.py"
    echo ""
    echo "🌐 Access the agent at: ws://localhost:8000"
else
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi