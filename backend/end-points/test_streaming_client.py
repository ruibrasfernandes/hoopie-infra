#!/usr/bin/env python3
"""
Test client for Hoopie Streaming Agent
Tests WebSocket connectivity and message handling for both text and audio modes
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

class StreamingAgentTestClient:
    def __init__(self, host="localhost", port=8000):
        self.host = host
        self.port = port
        self.websocket = None
        self.session_id = "test-session-123"

    async def connect(self, is_audio=False):
        """Connect to the streaming agent WebSocket"""
        uri = f"ws://{self.host}:{self.port}/ws/{self.session_id}?is_audio={str(is_audio).lower()}"
        print(f"🔌 Connecting to: {uri}")

        try:
            self.websocket = await websockets.connect(uri)
            print(f"✅ Connected successfully!")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    async def send_text_message(self, message):
        """Send a text message to the agent"""
        if not self.websocket:
            print("❌ Not connected to WebSocket")
            return False

        message_obj = {
            "mime_type": "text/plain",
            "data": message
        }

        print(f"📤 Sending: {message}")
        await self.websocket.send(json.dumps(message_obj))
        return True

    async def listen_for_responses(self, timeout=30):
        """Listen for responses from the agent"""
        response_text = ""
        start_time = asyncio.get_event_loop().time()

        try:
            while True:
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    print(f"⏰ Timeout after {timeout} seconds")
                    break

                # Wait for message with timeout
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
                    response = json.loads(message)

                    print(f"📥 Received: {response}")

                    # Handle turn completion
                    if response.get("turn_complete"):
                        print("✅ Turn completed")
                        break

                    # Handle interruption
                    if response.get("interrupted"):
                        print("🛑 Turn interrupted")
                        break

                    # Handle text response
                    if response.get("mime_type") == "text/plain":
                        response_text += response.get("data", "")

                    # Handle audio response
                    if response.get("mime_type") == "audio/pcm":
                        audio_data = response.get("data", "")
                        print(f"🔊 Received audio data: {len(audio_data)} bytes (base64)")

                except asyncio.TimeoutError:
                    print("⏰ No response within 5 seconds, continuing...")
                    continue

        except Exception as e:
            print(f"❌ Error listening for responses: {e}")

        return response_text

    async def disconnect(self):
        """Disconnect from WebSocket"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 Disconnected")

async def test_text_mode():
    """Test text-only interaction"""
    print("\n" + "="*50)
    print("🧪 TESTING TEXT MODE")
    print("="*50)

    client = StreamingAgentTestClient()

    # Connect
    if not await client.connect(is_audio=False):
        return False

    # Send test message
    test_message = "What time is it?"
    await client.send_text_message(test_message)

    # Listen for response
    response = await client.listen_for_responses(timeout=30)

    # Validate response
    if response:
        print(f"✅ Received response: {response}")
        success = "time" in response.lower() or len(response) > 10
        print(f"✅ Test {'PASSED' if success else 'FAILED'}")
    else:
        print("❌ No response received")
        success = False

    await client.disconnect()
    return success

async def test_audio_mode():
    """Test audio mode connection (without actual audio data)"""
    print("\n" + "="*50)
    print("🧪 TESTING AUDIO MODE CONNECTION")
    print("="*50)

    client = StreamingAgentTestClient()

    # Connect in audio mode
    if not await client.connect(is_audio=True):
        return False

    print("✅ Audio mode connection successful")

    # Send a text message even in audio mode (should still work)
    await client.send_text_message("Hello in audio mode")

    # Listen for response
    response = await client.listen_for_responses(timeout=15)

    success = bool(response)
    print(f"✅ Audio mode test {'PASSED' if success else 'FAILED'}")

    await client.disconnect()
    return success

async def test_connection_robustness():
    """Test connection handling and error scenarios"""
    print("\n" + "="*50)
    print("🧪 TESTING CONNECTION ROBUSTNESS")
    print("="*50)

    # Test invalid host
    client = StreamingAgentTestClient(host="invalid-host")
    success = await client.connect()
    if success:
        print("❌ Should have failed to connect to invalid host")
        await client.disconnect()
        return False
    else:
        print("✅ Correctly failed to connect to invalid host")

    # Test invalid port
    client = StreamingAgentTestClient(port=9999)
    success = await client.connect()
    if success:
        print("❌ Should have failed to connect to invalid port")
        await client.disconnect()
        return False
    else:
        print("✅ Correctly failed to connect to invalid port")

    return True

async def main():
    """Run all tests"""
    print("🚀 Starting Hoopie Streaming Agent Test Suite")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    tests = [
        ("Connection Robustness", test_connection_robustness),
        ("Text Mode", test_text_mode),
        ("Audio Mode", test_audio_mode),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)

    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n📈 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! Streaming agent is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the streaming agent setup.")
        return 1

if __name__ == "__main__":
    print("Hoopie Streaming Agent Test Client")
    print("Make sure the streaming agent is running on localhost:8000")
    print("Usage: python test_streaming_client.py")
    print()

    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)