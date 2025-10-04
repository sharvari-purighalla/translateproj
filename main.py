import translateproj.transcribe as transcribe
import translateproj.translate as translate

# --- config ---
REGION = "us-east-1"                       # your region           
BUCKET = "sharvaristranscribebucket"       # your S3 bucket's name 
INPUT_PREFIX = "audio/"                    # where your audio files go in S3
OUTPUT_PREFIX = "transcripts/"             # where your transcripts go in S3
SAMPLE_RATE = 16000                        
CHANNELS = 1
BITS = "PCM_16"    
TRANSCRIPT_KEY = "transcripts/5f45340d57fb4c518e472d936c0031b1.txt"



