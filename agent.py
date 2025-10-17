import asyncio
import pyaudio
import websockets
import uuid
import base64
import json
import superu

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

async def listen_and_send(uri, streamId):
    stream = await asyncio.to_thread(
        pya.open, format=FORMAT, channels=CHANNELS, rate=SEND_SAMPLE_RATE,
        input=True, input_device_index=mic_index, frames_per_buffer=CHUNK_SIZE)
    
    import urllib.parse

    encoded_token = urllib.parse.quote(pluto['ws_url'].split('/')[-1], safe='')
    uri = f"ws://pluto-ws.superu.ai/connect_call/{pluto['call_id']}/{encoded_token}"

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

import os
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
        voice_id="90ipbRoKi4CpHXvKVtl0"  # Anika - Customer Care Agent
    )
    # print(json.dumps(pluto, indent=2))
    asyncio.run(listen_and_send(pluto['ws_url'], pluto['streamId']))