import requests
from dotenv import load_dotenv
import os
import openai

# Load environment variables
load_dotenv()


async def extract_transcript_from_deepgram(video_file_path, content_type):
    api_key = os.getenv('DEEPGRAM_API_KEY')
    url = 'https://api.deepgram.com/v1/listen?smart_format=true&language=en&model=nova-2&diarize=true&punctuate=true&utterances=true'
    headers = {
        'Authorization': f'Token {api_key}',
        'Content-Type': content_type
    }
    with open(video_file_path, 'rb') as file:
        response = requests.post(url, headers=headers, data=file)
    response.raise_for_status()
    data = response.json()
    transcript = data['results']['channels'][0]['alternatives'][0]['transcript']
    return transcript


def is_transcript_usable(transcript: str) -> bool:
    api_token = os.getenv("MISTRAL_API_KEY")
    client = openai.OpenAI(
        base_url="https://api.mistral.ai/v1",
        api_key=api_token
    )

    prompt = f"""
    Does the following video segment have speech? Are people talking in it, in a way that needs to be explicitly transcribed?
    
    Basically, if the video is a conversation to the camera, and the speaker is or speakers are talking to the camera or being overheard very clearly by the camera, then this is a usable transcript.
    
    Otherwise, it is background footage. Still useful, but the answer should be "no".
    
    Answer with a final "yes" or "no".
    
    Video Transcript: {transcript}

    Has Speech?
    """

    print(prompt)

    chat_completion = client.chat.completions.create(
        model="mistral-medium",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=1
    )

    answer = chat_completion.choices[0].message.content.strip().lower()
    print(f"Answer about whether transcript has speech: {answer}")
    return "yes" in answer


def tidy_transcript(description: str, raw_transcript: str, duration: float) -> str:
    api_token = os.getenv("MISTRAL_API_KEY")
    client = openai.OpenAI(
        base_url="https://api.mistral.ai/v1",
        api_key=api_token
    )

    prompt = f"""
    Please name speakers in the raw_transcript if their names are anywhere in the context. DO NOT ADD ANY CONTENT.
    
    video_description: {description}
    duration: {duration} seconds

    PLEASE ONLY RETURN THE TRANSCRIPT WITH SPEAKERS NAMED. DO NOT ADD ANY OTHER COMMENTS OR CONTENT OTHER THAN THE FINAL TRANSCRIPT.
    
    raw_transcript: {raw_transcript}
    

    tidy_transcript:
    """

    # print(prompt)

    chat_completion = client.chat.completions.create(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": "You are a video editor screenwriting and then cutting a TV news / social media video."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=1000
    )

    answer = chat_completion.choices[0].message.content.strip()
    print(f"tidy transcript: {answer}")
    return answer
