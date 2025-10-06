# audio.py
import numpy as np
import sounddevice as sd
import soundfile as sf
from pynput import keyboard
import threading
import time

SAMPLE_RATE = 16000
CHANNELS = 1
BITS = "PCM_16"

_is_recording = False
_recording_chunks = []
_stream = None
_lock = threading.Lock()

def _record_worker():
    """Background thread that pulls audio chunks while recording."""
    global _stream, _recording_chunks
    with _lock:
        _recording_chunks = []
    _stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16")
    _stream.start()
    print("[rec] Recording… press 'q' again to stop.")

    while True:
        with _lock:
            if not _is_recording:
                break
        data, _ = _stream.read(2048)
        with _lock:
            _recording_chunks.append(data)

    _stream.stop()
    _stream.close()
    _stream = None

def record_wav_on_q_toggle(out_path: str = "recorded_audio.wav") -> str | None:
    """Press Q to start/stop recording. Saves .wav and returns the path."""
    saved_path = None

    def on_press(key):
        nonlocal saved_path
        global _is_recording, _recording_chunks
        try:
            if key.char.lower() == "q":
                with _lock:
                    starting = not _is_recording
                    _is_recording = not _is_recording

                if starting:
                    threading.Thread(target=_record_worker, daemon=True).start()
                else:
                    print("[rec] Stopping…")
                    time.sleep(0.06)

                    with _lock:
                        chunks = list(_recording_chunks)

                    if not chunks:
                        print("[rec] No audio captured (stopped too quickly). Try again.")
                        saved_path = None
                    else:
                        audio = np.concatenate(chunks, axis=0)
                        sf.write(out_path, audio, SAMPLE_RATE, subtype=BITS)
                        print(f"[rec] Saved {out_path}")
                        saved_path = out_path
                    return False
        except AttributeError:
            pass

    print("Press 'q' to start recording, and press 'q' again to stop.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    return saved_path

if __name__ == "__main__":
    record_wav_on_q_toggle("test_record.wav")