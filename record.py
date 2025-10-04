import sounddevice as sd
import soundfile as sf
import keyboard
import numpy as np
import time

SAMPLE_RATE = 16000
CHANNELS = 1
BITS = "PCM_16"

def record_while_space_pressed(local_path="output.wav"):
    print("Press and hold SPACE to record. Release to stop.")
    recording = []
    is_recording = False
    stream = None

    while True:
        if keyboard.is_pressed('space'):
            if not is_recording:
                print("[rec] Recording started...")
                is_recording = True
                stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16')
                stream.start()
            # read small chunks while space is pressed
            data, _ = stream.read(1024)
            recording.append(data)
        else:
            if is_recording:
                print("[rec] Recording stopped.")
                is_recording = False
                stream.stop()
                stream.close()
                audio = np.concatenate(recording, axis=0)
                sf.write(local_path, audio, SAMPLE_RATE, subtype=BITS)
                print(f"[rec] Saved {local_path}")
                break
        time.sleep(0.01)  # prevents CPU overuse

record_while_space_pressed("recorded_audio.wav")
