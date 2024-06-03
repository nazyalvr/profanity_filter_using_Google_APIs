from flask import *
from google.cloud import speech
import os
import io
import json
import wave

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google_secret_key.json'
client = speech.SpeechClient()

app = Flask(__name__)
f = open("en_bad_words.json")
jsonArray = json.load(f)

file_name = "mat_ukr_ru.txt"
file1 = open(file_name, 'r', encoding='utf-16-le')
all_profanity_words = file1.read().splitlines()
all_profanity_words.extend(jsonArray)


def find_profanity_words(transcript):
    list_result = []
    for result in transcript:
        alternative = result.alternatives[0]
        for word_info in alternative.words:
            word = word_info.word.lower()
            if word in all_profanity_words:
                start_time = word_info.start_time
                end_time = word_info.end_time
                list_result.append(
                    f"Word: {word}, start_time: {start_time.total_seconds()}, end_time: {end_time.total_seconds()}")
    return list_result


@app.get("/prof")
def get_profanity():
    URL = request.args.get("URL")
    lang = request.args.get("lang")
    file_name = "audio.wav"
    import httplib2
    h = httplib2.Http(".cache")
    resp, content = h.request(URL, "GET")
    open(file_name, "wb").write(content)

    wave_file = wave.open(file_name, "r")
    channel_count = wave_file.getnchannels()
    wave_file.close()

    with io.open(file_name, "rb") as audio_file:
        content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(
        language_code=lang,
        enable_word_time_offsets=True,
        audio_channel_count=channel_count,
    )

    response = client.long_running_recognize(request={"config": config, "audio": audio})
    json_list = find_profanity_words(response.results)
    output = json.dumps({"profanity_count": len(json_list), "value": json_list})
    return output, 200


if __name__ == '__main__':
    app.run()
