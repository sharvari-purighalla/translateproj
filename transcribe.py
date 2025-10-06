# transcribe.py
import uuid
import time
import requests
import boto3

def upload_to_s3(region, bucket, local_file, key):
    s3 = boto3.client("s3", region_name=region)
    s3.upload_file(local_file, bucket, key)
    print(f"[s3] Uploaded -> s3://{bucket}/{key}")
    return f"s3://{bucket}/{key}"

def put_text_to_s3(region, bucket, key, text):
    s3 = boto3.client("s3", region_name=region)
    s3.put_object(
        Bucket=bucket, Key=key, Body=text.encode("utf-8"),
        ContentType="text/plain; charset=utf-8"
    )
    print(f"[s3] Transcript saved -> s3://{bucket}/{key}")

def start_transcribe_job(region, bucket, s3_key, language_code=None,
                         identify_language=True, language_options=None):
    transcribe = boto3.client("transcribe", region_name=region)
    job_name = f"job-{uuid.uuid4().hex}"
    media_uri = f"s3://{bucket}/{s3_key}"

    params = dict(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": media_uri},
        MediaFormat="wav",
    )

    if identify_language:
        params["IdentifyLanguage"] = True
        if language_options:
            params["LanguageOptions"] = language_options
    else:
        params["LanguageCode"] = language_code or "en-US"

    transcribe.start_transcription_job(**params)
    print(f"[tx] Started job: {job_name}")
    return job_name

def wait_get_transcript(region, job_name):
    """Waits for the job to finish, returns (text, json_uri, lang)."""
    client = boto3.client("transcribe", region_name=region)
    while True:
        job = client.get_transcription_job(TranscriptionJobName=job_name)["TranscriptionJob"]
        status = job["TranscriptionJobStatus"]
        if status in ("COMPLETED", "FAILED"):
            break
        time.sleep(2)

    if status == "FAILED":
        raise RuntimeError(f"Transcribe failed: {job}")

    json_uri = job["Transcript"]["TranscriptFileUri"]
    data = requests.get(json_uri).json()
    text = data.get("results", {}).get("transcripts", [{}])[0].get("transcript", "")
    lang = job.get("LanguageCode", "unknown")
    return text, json_uri, lang

def transcribe_wav_file(region, bucket, input_prefix, output_prefix,
                        local_wav_path, language_options=None,
                        force_language_code=None):
    audio_key = f"{input_prefix}{uuid.uuid4().hex}.wav"
    upload_to_s3(region, bucket, local_wav_path, audio_key)

    job = start_transcribe_job(
        region, bucket, audio_key,
        language_code=force_language_code,
        identify_language=force_language_code is None,
        language_options=language_options,
    )

    text, json_uri, lang = wait_get_transcript(region, job)
    print(f"[tx] Detected language: {lang}")

    transcript_key = f"{output_prefix}{uuid.uuid4().hex}.txt"
    put_text_to_s3(region, bucket, transcript_key, text)

    return text, lang, audio_key, transcript_key
