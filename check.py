import pyaudio
pya = pyaudio.PyAudio()

def get_default_input_device_index():
    for i in range(pya.get_device_count()):
        dev = pya.get_device_info_by_index(i)
        if dev['maxInputChannels'] > 0:
            print(f"Using device: {dev['name']} (Index: {i})")
            return i
    raise RuntimeError("No input device found.")

mic_index = get_default_input_device_index()

dev_info = pya.get_device_info_by_index(mic_index)
print(dev_info)
