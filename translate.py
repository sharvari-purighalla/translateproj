# translate.py
"""
Light wrapper around Amazon Translate.
"""

from __future__ import annotations
from typing import Optional
import boto3


def to_translate_code(transcribe_lang_code: Optional[str]) -> str:
    """
    Convert a Transcribe code like 'en-US' to a Translate code 'en'.
    If unknown/None, return 'auto' to let Translate detect source.
    """
    if not transcribe_lang_code or transcribe_lang_code == "unknown":
        return "auto"
    return transcribe_lang_code.split("-")[0]


def translate_text(region: str, text: str, src_code: str, tgt_code: str) -> str:
    """
    Call Amazon Translate. 'src_code' can be 'auto' or a 2-letter code.
    'tgt_code' must be a valid Translate target (e.g. 'en', 'es', 'fr', 'hi').
    """
    client = boto3.client("translate", region_name=region)
    resp = client.translate_text(
        Text=text,
        SourceLanguageCode=src_code if src_code else "auto",
        TargetLanguageCode=tgt_code,
    )
    return resp["TranslatedText"]
