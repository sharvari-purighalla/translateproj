# transcribe.py
"""
Helpers to:
  - upload a local WAV to S3
  - start an Amazon Transcribe job (auto-detect or fixed language)
  - poll for completion
  - save the plain text transcript back to S3

Returns (text, detected_lang, audio_key, transcript_text_key)
"""

from __future__ import annotations
import uuid
import time
from typing import Tuple, Optional, List

import requests
import boto3
from botocore.exceptions import BotoCoreError, ClientError


def upload_to_s3(region: str, bucket: str, local_file: str, key: str) -> str:
    s3 = boto3.client("s3", region_name=region)
    s3.upload_file(local_file, bucket, key)
    print(f"[s3] Uploaded -> s3://{bucket}/{key}")
    return f"s3://{bucket}/{key}"


def put_text_to_s3(region: str, bucket: str, key: str, text: str) -> None:
    s3 = boto3.client("s3", region_name=region)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=text.encode("utf-8"),
        ContentType="text/plain; charset=utf-8",
    )
    print(f"[s3] Transcript saved -> s3://{bucket}/{key}")


def start_transcribe_job(
    region: str,
    bucket: str,
    s3_key: str,
    language_code: Optional[str] = None,
    identify_language: bool = True,
    language_options: Optional[List[str]] = None,
) -> str:

    # starts a Transcribe job against s3://bucket/s3_key.
    # if language_code is provided, IdentifyLanguage must be False.

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


def wait_get_transcript(region: str, job_name: str, timeout_sec: int = 600) -> Tuple[str, str, str]:
    """
    Polls the job until COMPLETED or FAILED (up to timeout_sec).
    Returns (plain_text, transcript_json_uri, detected_language_code).
    """
    client = boto3.client("transcribe", region_name=region)
    start = time.time()

    while True:
        job = client.get_transcription_job(TranscriptionJobName=job_name)["TranscriptionJob"]
        status = job["TranscriptionJobStatus"]

        if status in ("COMPLETED", "FAILED"):
            break

        if time.time() - start > timeout_sec:
            raise TimeoutError(f"Transcribe job timed out: {job_name}")

        time.sleep(2)

    if status == "FAILED":
        raise RuntimeError(f"Transcribe failed: {job}")

    json_uri = job["Transcript"]["TranscriptFileUri"]
    data = requests.get(json_uri).json()
    text = data.get("results", {}).get("transcripts", [{}])[0].get("transcript", "")
    lang = job.get("LanguageCode", "unknown")
    return text, json_uri, lang


def transcribe_wav_file(
    region: str,
    bucket: str,
    input_prefix: str,
    output_prefix: str,
    local_wav_path: str,
    language_options: Optional[List[str]] = None,
    force_language_code: Optional[str] = None,
) -> Tuple[str, str, str, str]:
    """
    Uploads local WAV, starts a job (auto-detect by default), waits for result,
    and uploads the plain-text transcript to S3.

    Returns: (text, detected_lang, audio_key, transcript_text_key)
    """
    audio_key = f"{input_prefix}{uuid.uuid4().hex}.wav"
    upload_to_s3(region, bucket, local_wav_path, audio_key)

    job = start_transcribe_job(
        region=region,
        bucket=bucket,
        s3_key=audio_key,
        language_code=force_language_code,
        identify_language=force_language_code is None,
        language_options=language_options,
    )

    text, json_uri, lang = wait_get_transcript(region, job)
    print(f"[tx] Detected language: {lang}")

    transcript_key = f"{output_prefix}{uuid.uuid4().hex}.txt"
    put_text_to_s3(region, bucket, transcript_key, text)
    return text, lang, audio_key, transcript_key
