# audio.py
"""
Press 'q' to start recording from the default input device (mic),
press 'q' again to stop. Saves a 16kHz mono PCM WAV and returns the path.

Dependencies:
  - sounddevice (PortAudio)
  - soundfile
  - pynput
On macOS, you may need: xcode-select --install && brew install portaudio
"""

from __future__ import annotations
import time
import threading
from typing import Optional, List

import numpy as np
import sounddevice as sd
import soundfile as sf
from pynput import keyboard

# audio settings
SAMPLE_RATE = 16_000          
CHANNELS = 1                
BITS = "PCM_16"             

_is_recording = False
_recording_chunks: List[np.ndarray] = []
_stream: Optional[sd.InputStream] = None
_lock = threading.Lock()



def _record_worker() -> None:
    # background thread that pulls audio frames while _is_recording is True.

    global _stream, _recording_chunks
    with _lock:
        _recording_chunks = []

    _stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16"
    )
    _stream.start()
    print("[rec] Recording… press 'q' again to stop.")

    while True:
        with _lock:
            if not _is_recording:
                break
        # Pull ~128ms per chunk (2048 samples @16kHz)
        data, _ = _stream.read(2048)
        with _lock:
            _recording_chunks.append(data)

    _stream.stop()
    _stream.close()
    _stream = None


def record_wav_on_q_toggle(out_path: str = "recorded_audio.wav") -> Optional[str]:
    """
    Show a keyboard listener; toggle recording with the 'q' key.
    When stopped, writes 'out_path' and returns it, or returns None if no audio captured.
    """
    saved_path: Optional[str] = None

    def on_press(key):
        nonlocal saved_path
        global _is_recording, _recording_chunks

        try:
            if key.char.lower() != "q":
                return
        except AttributeError:
            # non-character (e.g., arrow keys) — ignore
            return

        # toggle under lock
        with _lock:
            starting = not _is_recording
            _is_recording = not _is_recording

        if starting:
            threading.Thread(target=_record_worker, daemon=True).start()
        else:
            print("[rec] Stopping…")
            # small delay so the worker can push the final chunk
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

            return False  # stop the listener

    
    print("Press 'q' to start recording, and press 'q' again to stop.")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

    return saved_path


if __name__ == "__main__":
    record_wav_on_q_toggle("test_record.wav")