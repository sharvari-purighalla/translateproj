import sounddevice as sd
import soundfile as sf
from pynput import keyboard
import numpy as np
import threading

SAMPLE_RATE = 16000
CHANNELS = 1
BITS = "PCM_16"

is_recording = False
recording_data = []
stream = None

def record_audio(file_name):
    global recording_data, stream, is_recording
    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16')
    stream.start()
    print("[rec] Recording started...")
    while is_recording:
        data, _ = stream.read(1024)
        recording_data.append(data)
    stream.stop()
    stream.close()

def on_press(key):
    global is_recording, recording_data
    try:
        if key.char == 'q':
            if not is_recording:
                recording_data = []
                is_recording = True
                threading.Thread(target=record_audio, daemon=True).start()
            else:
                is_recording = False
                print("[rec] Recording stopped.")
                audio = np.concatenate(recording_data, axis=0)
                sf.write("recorded_audio.wav", audio, SAMPLE_RATE, subtype=BITS)
                print("[rec] Saved recorded_audio.wav")
                return False  # stop listening
    except AttributeError:
        pass  # ignore special keys

print("Press 'q' to start recording, and press 'q' again to stop.")
with keyboard.Listener(on_press=on_press) as listener:
    listener.join()
