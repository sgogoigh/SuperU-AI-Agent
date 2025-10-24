import asyncio
import pyaudio
import websockets
import uuid
import base64
import json
import superu
import os

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 48000
CHUNK_SIZE = 1024
pya = pyaudio.PyAudio()

def get_default_input_device_index():
    for i in range(pya.get_device_count()):
        dev = pya.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print(f"Using device: {dev['name']} (Index: {i})")
            return i
    raise RuntimeError("No input device found.")

mic_index = get_default_input_device_index()

async def send_audio(stream, websocket, streamId):
    await websocket.send(json.dumps({"event": "start", "start": {"streamId": streamId}}))
    while True:
        audio_chunk = await asyncio.to_thread(stream.read, CHUNK_SIZE)
        payload = base64.b64encode(audio_chunk).decode('utf-8')
        await websocket.send(json.dumps({"event": "media", "media": {"payload": payload}}))

async def receive_messages(websocket):
    output_stream = await asyncio.to_thread(
        pya.open, format=FORMAT, channels=CHANNELS, rate=SEND_SAMPLE_RATE, output=True)
    while True:
        try:
            response = json.loads(await websocket.recv())
            if response.get("event") == "playAudio":
                audio_data = base64.b64decode(response["media"]["payload"])
                await asyncio.to_thread(output_stream.write, audio_data)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed.")
            break

async def listen_and_send(uri, streamId, api_key):

    print("Attempting to connect to websocket URI:", uri)
    if not uri:
        raise RuntimeError("No websocket URI provided (uri is falsy). Check pluto response.")

    # Basic validation of scheme
    if uri.startswith("http://") or uri.startswith("https://"):
        print("WARNING: URI uses http/https scheme. It must be ws:// or wss:// for WebSocket handshake.")
    if not (uri.startswith("ws://") or uri.startswith("wss://")):
        raise RuntimeError("ws_url must start with ws:// or wss://. Found: " + uri[:50])

    # Optional: attach Authorization header if you know the service needs it.
    extra_headers = None
    if api_key:
        extra_headers = [("Authorization", f"Bearer {api_key}")]
        print("Added Authorization header for handshake.")

    # Choose SSL context for wss
    ssl_ctx = None
    if uri.startswith("wss://"):
        ssl_ctx = ssl.create_default_context()
    
    try:
        print("Performing handshake test...")
        async with websockets.connect(uri, extra_headers=extra_headers, ssl=ssl_ctx) as ws:
            print("Handshake OK — server accepted connection.")
        print("Handshake test closed.")
    except Exception as e:
        print("Handshake test failed:", repr(e))
        raise


    stream = await asyncio.to_thread(
        pya.open, format=FORMAT, channels=CHANNELS, rate=SEND_SAMPLE_RATE,
        input=True, input_device_index=mic_index, frames_per_buffer=CHUNK_SIZE)
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket. Streaming audio...")
        try:
            await asyncio.gather(
                send_audio(stream, websocket, streamId),
                receive_messages(websocket))
        except Exception as e:
            print(f"Error: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            pya.terminate()
            print("Connection closed.")

from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    superu_client = superu.SuperU(os.getenv("SUPER_U_API_KEY"))
    First_message = "Hey there! Ready to explore some fascinating science today?"
    System_prompt = """
        You are a helpful and curious science assistant. Your job is to answer questions clearly, concisely, and in a way that's engaging for someone interested in science.
    """
    pluto = superu_client.pluto.create_call(
        first_message=First_message,
        system_prompt=System_prompt,
        model = "pluto_1.1",
        voice_id="90ipbRoKi4CpHXvKVtl0",  # Anika - Customer Care Agent
    )
    print(pluto["ws_url"])
    print()
    asyncio.run(listen_and_send(pluto['ws_url'], pluto['streamId'], os.getenv("SUPER_U_API_KEY")))