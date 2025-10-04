import transcribe
import translate
import audio

# --- config ---
region = "us-east-1"                       # your region           
bucket = "sharvaristranscribebucket"       # your S3 bucket's name 
input_prefix = "audio/"                    # where your audio files go in S3
output_prefix = "transcripts/"             # where your transcripts go in S3
sample_rate = 16000                        
channels = 1
bits = "PCM_16"    
transcript_key = "transcripts/5f45340d57fb4c518e472d936c0031b1.txt"

user_1_name = input(str("What is your name (Person 1) >>  "))
user_1_language = input(str("What language do you speak? (Person 1) >>  "))
user_2_name = input(str("What is your name (Person 2) >>  "))
user_2_language = input(str("What language do you speak? (Person 2) >>  "))

running = True
while running == True:
    print(f"{user_1_name} can talk now")
    audio.audio()
    transcribed_text = transcribe.speech_to_text(region,bucket,input_prefix,output_prefix,"recorded_audio")
    output_text = translate(region,bucket,transcript_key,transcribed_text,user_1_language,user_2_language)
    print(output_text)

    print(f"{user_2_name} can talk now")
    audio.audio()
    transcribed_text = transcribe.speech_to_text(region,bucket,input_prefix,output_prefix,"recorded_audio")
    output_text = translate.translate(region,bucket,transcript_key,transcribed_text,user_2_language,user_1_language)
    print(output_text)

audio.record_audio()


