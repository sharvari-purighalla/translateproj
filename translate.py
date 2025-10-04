import boto3


def translate(region,bucket,transcript_key,text,in_lang,out_lang):
    # read transcript text from S3
    s3 = boto3.client("s3", region_name=region)
    obj = s3.get_object(Bucket=bucket, Key=transcript_key)
    text = obj["Body"].read().decode("utf-8")


    # translate the text
    translate = boto3.client("translate", region_name=region) # create a translate client

    # ask amazon translate to detect teh source language and translate to target languagae
    resp = translate.translate_text(Text=text, SourceLanguageCode=in_lang, TargetLanguageCode=out_lang)

    # output translated text
    return resp["TranslatedText"]
