# Hoopie Streaming Agent

WebSocket-based streaming agent for real-time voice and text interactions using Google ADK.

## Quick Start

1. **Setup Dependencies**
   ```bash
   cd backend/end-points
   ./setup.sh
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the Server**
   ```bash
   export GOOGLE_GENAI_USE_VERTEXAI=TRUE
   export GOOGLE_CLOUD_PROJECT=hoopie-dev
   export GOOGLE_CLOUD_LOCATION=us-central1

   uv run uvicorn streaming_agent:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Test the Connection**
   ```bash
   python test_streaming_client.py
   ```

## Environment Configuration

### Required Variables
```bash
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=hoopie-dev
GOOGLE_CLOUD_LOCATION=us-central1  # Required for streaming models
```

### Optional Variables
```bash
SSL_CERT_FILE=/path/to/certificates  # If SSL is required
HOST=0.0.0.0
PORT=8000
```

## WebSocket API

### Connection
- **URL**: `ws://localhost:8000/ws/{session_id}?is_audio={true|false}`
- **Authentication**: None (for development)

### Message Format

#### Text Message (Send)
```json
{
  "mime_type": "text/plain",
  "data": "What time is it?"
}
```

#### Audio Message (Send)
```json
{
  "mime_type": "audio/pcm",
  "data": "base64encodedaudiodata"
}
```

#### Response Messages
```json
{
  "mime_type": "text/plain",
  "data": "It is currently 3:45 PM"
}

{
  "mime_type": "audio/pcm",
  "data": "base64encodedaudiodata"
}

{
  "turn_complete": true,
  "interrupted": false
}
```

## Architecture

```
Client (hoopie-web) → WebSocket → streaming_agent.py → ADK InMemoryRunner → hoopie_sdm agent
```

### Key Components
- **FastAPI**: WebSocket server framework
- **Google ADK**: Agent Development Kit for streaming
- **InMemoryRunner**: Manages agent sessions
- **LiveRequestQueue**: Handles bidirectional communication
- **hoopie_sdm.agent**: The actual Hoopie agent

## Development

### Running with Auto-reload
```bash
uv run uvicorn streaming_agent:app --host 0.0.0.0 --port 8000 --reload
```

### Testing
```bash
# Run test suite
python test_streaming_client.py

# Test specific functionality
python -c "
import asyncio
from test_streaming_client import test_text_mode
asyncio.run(test_text_mode())
"
```

### Debugging
- Check logs for WebSocket connection issues
- Verify environment variables are set correctly
- Ensure hoopie-adk agent is accessible
- Test with simple text messages first

## Troubleshooting

### Common Issues

1. **Port 8000 already in use**
   ```bash
   sudo lsof -ti:8000 | xargs kill -9
   ```

2. **Import errors for hoopie_sdm**
   ```bash
   # Ensure the path is correct
   ls ../../hoopie-adk/hoopie_sdm/agent.py
   ```

3. **Vertex AI region issues**
   ```bash
   # Make sure region is us-central1
   export GOOGLE_CLOUD_LOCATION=us-central1
   ```

4. **Audio not working**
   - Check browser permissions for microphone
   - Verify WebSocket connection in audio mode
   - Test with text messages first

### Error Messages
- `ModuleNotFoundError: hoopie_sdm` → Check sys.path configuration
- `Connection refused` → Ensure server is running on port 8000
- `WebSocket timeout` → Check network connectivity
- `Audio worklet failed` → Check browser audio API support

## Files

- `streaming_agent.py` - Main WebSocket server
- `test_streaming_client.py` - Test client for validation
- `setup.sh` - Automated setup script
- `requirements.txt` - Python dependencies
- `.env.example` - Environment template