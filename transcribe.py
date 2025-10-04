import os, uuid, time, io, argparse
import requests
import boto3
import sounddevice as sd
import soundfile as sf

# --- config ---
REGION = "us-east-2"                       # your region           
BUCKET = "sharvaristranscribebucket"       # your S3 bucket's name 
INPUT_PREFIX = "audio/"                    # where your audio files go in S3
OUTPUT_PREFIX = "transcripts/"             # where your transcripts go in S3
SAMPLE_RATE = 16000                        
CHANNELS = 1
BITS = "PCM_16"                           

def speech_to_text(region,bucket,input_prefix,output_prefix,sample_rate,channels,bits,):
s3 = boto3.client("s3", region_name=REGION)
transcribe = boto3.client("transcribe", region_name=REGION)

# record the audio for a set no of seconds
def record_wav(local_path: str, seconds: int = 10):
    print(f"[rec] Recording {seconds}s @ {SAMPLE_RATE} Hz mono…")
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16')
    sd.wait()
    sf.write(local_path, audio, SAMPLE_RATE, subtype=BITS)
    print(f"[rec] Saved {local_path}")

# upload the .wav to S3 bucket
def upload_to_s3(local_path: str, key: str):
    s3.upload_file(local_path, BUCKET, key)
    print(f"[s3] Uploaded -> s3://{BUCKET}/{key}")

# transcribe job
def start_transcribe_job(s3_key: str, *, language_code: str | None, identify_language: bool, language_options: list[str] | None):
    job_name = f"job-{uuid.uuid4().hex}"
    media_uri = f"s3://{BUCKET}/{s3_key}"

    params = dict(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": media_uri},
        MediaFormat="wav",               # matches what we recorded
    )

    # choose either fixed language or auto-detect
    if identify_language:
        params["IdentifyLanguage"] = True
        if language_options:
            params["LanguageOptions"] = language_options
    else:
        params["LanguageCode"] = language_code or "en-US"

    transcribe.start_transcription_job(**params)
    print(f"[tx] Started job: {job_name}")
    return job_name

# get the text
def wait_for_job_and_get_text(job_name: str) -> tuple[str, str, str]:
    """Returns (plain_text, transcript_json_uri, detected_language_code)."""
    while True:
        resp = transcribe.get_transcription_job(TranscriptionJobName=job_name)["TranscriptionJob"]
        status = resp["TranscriptionJobStatus"]
        if status in ("COMPLETED", "FAILED"):
            break
        time.sleep(2)

    if status == "FAILED":
        raise RuntimeError(f"Transcribe failed: {resp}")

    json_uri = resp["Transcript"]["TranscriptFileUri"]
    data = requests.get(json_uri).json()
    text = data["results"]["transcripts"][0]["transcript"] if data["results"]["transcripts"] else ""
    lang = resp.get("LanguageCode", "unknown")
    return text, json_uri, lang


# upload the transcript to the S3 bucket
def put_transcript_text_to_s3(text: str, key: str):
    s3.put_object(Bucket=BUCKET, Key=key, Body=text.encode("utf-8"), ContentType="text/plain; charset=utf-8")
    print(f"[s3] Transcript text saved -> s3://{BUCKET}/{key}")



def main():
    parser = argparse.ArgumentParser(description="Record, upload, transcribe, save transcript to S3.")
    parser.add_argument("--seconds", type=int, default=6, help="Record duration (seconds)")
    parser.add_argument("--lang", type=str, default=None, help="Explicit language code (e.g., en-US, es-ES). If omitted, auto-detect.")
    parser.add_argument("--lang-options", type=str, default="en-US,es-ES,fr-FR", help="Comma list for auto-detect shortlist")
    args = parser.parse_args()

    # 1) record
    local_wav = f"clip_{uuid.uuid4().hex}.wav"
    record_wav(local_wav, seconds=args.seconds)

    # 2) upload audio to S3
    audio_key = f"{INPUT_PREFIX}{uuid.uuid4().hex}.wav"
    upload_to_s3(local_wav, audio_key)

    # 3) start job
    identify = args.lang is None
    job_name = start_transcribe_job(
        s3_key=audio_key,
        language_code=args.lang,
        identify_language=identify,
        language_options=[x.strip() for x in args.lang_options.split(",")] if identify else None,
    )

    # 4) wait + get transcript
    text, json_uri, lang = wait_for_job_and_get_text(job_name)

    print("\n=== TRANSCRIBED TEXT ===")
    print(text)
    print(f"\n[info] Detected/used language: {lang}")
    print(f"[info] Transcript JSON: {json_uri}")

    # 5) save a clean .txt into S3 
    transcript_key = f"{OUTPUT_PREFIX}{uuid.uuid4().hex}.txt"
    put_transcript_text_to_s3(text, transcript_key)

    # 6) print keys for your translate step
    print(f"\n[done] Audio:      s3://{BUCKET}/{audio_key}")
    print(f"[done] Transcript: s3://{BUCKET}/{transcript_key}")

    # cleanup local file
    try:
        os.remove(local_wav)
    except Exception:
        pass

if __name__ == "__main__":
    main()