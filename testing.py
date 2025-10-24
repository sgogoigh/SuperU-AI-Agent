import asyncio
import websockets

async def test_ws_connection(uri):
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

if __name__ == "__main__":
    # Paste the exact ws_url from SuperU here
    uri = "ws://pluto-ws.superu.ai/connect_call/..."  # Replace with actual value
    asyncio.run(test_ws_connection(uri))