# translate.py
import boto3

def to_translate_code(transcribe_lang_code):
    """Convert 'en-US' -> 'en' for Translate."""
    if not transcribe_lang_code or transcribe_lang_code == "unknown":
        return "auto"
    return transcribe_lang_code.split("-")[0]

def translate_text(region, text, src_code, tgt_code):
    client = boto3.client("translate", region_name=region)
    resp = client.translate_text(
        Text=text,
        SourceLanguageCode=src_code if src_code else "auto",
        TargetLanguageCode=tgt_code
    )
    return resp["TranslatedText"]
