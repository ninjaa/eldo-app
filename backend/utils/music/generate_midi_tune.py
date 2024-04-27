import base64
import replicate
import subprocess
import datetime
import mido
import random

# alright so the real process is ... hit gemini with a prompt
# then pipe that to the midi file
# then convert that to mp3
# then return the mp3 file

import os
import requests
import json

import re
from dotenv import load_dotenv
load_dotenv()


def extract_last_triple_backticks(text):
    # Extract content within triple backticks
    results = re.findall(r'```(.*?)```', text, re.DOTALL)
    return results[-1].strip() if results else None


def fetch_generation_pattern(c2m_command, musicprompt):
    prompt_id = '1b400a30-c7e6-4cfd-9518-5412e94f280f'
    api_key = os.getenv("WORDWARE_API_KEY")
    response = requests.post(
        f"https://app.wordware.ai/api/prompt/{prompt_id}/run",
        json={"inputs": {"c2m_command": c2m_command, "musicprompt": musicprompt}},
        headers={"Authorization": f"Bearer {api_key}"},
        stream=True
    )

    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                content = json.loads(line.decode('utf-8'))
                if content.get('type') == "chunk" and content.get('value', {}).get('type') == "outputs":
                    generation_pattern_response = content.get('value', {}).get(
                        'values', {}).get('generation_pattern', None)
                    if generation_pattern_response is not None:
                        return extract_last_triple_backticks(generation_pattern_response)
                    else:
                        print("Key 'generation_pattern' not found in the response.")
                        return None
    else:
        print(f"Failed to fetch data, status code: {response.status_code}")
        return None


def fetch_c2m_tune(musicprompt, debug=False):
    prompt_id = 'bf4dee5c-076d-4b09-bccb-2cb3198176b6'
    api_key = os.getenv("WORDWARE_API_KEY")
    # Execute the prompt with the appropriate input
    response = requests.post(f"https://app.wordware.ai/api/prompt/{prompt_id}/run",
                             json={"inputs": {"musicprompt": musicprompt}},
                             headers={"Authorization": f"Bearer {api_key}"},
                             stream=True)

    print(response.status_code)

    # Process the response
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                content = json.loads(line.decode('utf-8'))
                print(content) if debug else None
                if content.get('type') == "chunk" and content.get('value', {}).get('type') == "outputs":
                    c2m_command_generation_response = content.get('value', {}).get(
                        'values', {}).get('c2m_command_generation', None)
                    if c2m_command_generation_response is not None:
                        c2m_command = extract_last_triple_backticks(
                            c2m_command_generation_response)
                        return c2m_command
                    else:
                        print(
                            "Key 'c2m_command_generation' not found in the response.")
                        return False
    else:
        print(f"Failed to fetch data, status code: {response.status_code}")
        return False


def generate_midi_tune(mood, tempo, num_notes):
    # Create a new MIDI file
    midi_file = mido.MidiFile()
    track = mido.MidiTrack()
    midi_file.tracks.append(track)

    # Set the tempo
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo)))

    # Define the mood-based note ranges and velocities
    if mood == 'happy':
        note_range = range(60, 85)  # Higher notes for a happy mood
        velocity_range = range(80, 110)  # Higher velocities for a happy mood
    elif mood == 'sad':
        note_range = range(45, 70)  # Lower notes for a sad mood
        velocity_range = range(50, 80)  # Lower velocities for a sad mood
    else:
        note_range = range(45, 85)  # Neutral note range
        velocity_range = range(50, 110)  # Neutral velocity range

    # Generate random notes based on the mood
    for _ in range(num_notes):
        note = random.choice(note_range)
        velocity = random.choice(velocity_range)
        track.append(mido.Message(
            'note_on', note=note, velocity=velocity, time=0))
        track.append(mido.Message('note_off', note=note,
                     velocity=velocity, time=480))

    # Save the MIDI file
    midi_filename = f'{mood}_tune.mid'
    midi_file.save(midi_filename)

    return midi_filename


def convert_midi_to_mp3(midi_file, mp3_file, soundfont_file='/usr/share/sounds/sf2/FluidR3_GM.sf2'):
    # Generate a unique temporary filename with a timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_file = f"output_{timestamp}.raw"

    # Convert MIDI to raw audio using FluidSynth
    fluidsynth_cmd = [
        'fluidsynth',
        '-ni',
        '-F', temp_file,
        soundfont_file,
        midi_file
    ]
    subprocess.run(fluidsynth_cmd, check=True)

    # Convert raw audio to MP3 using LAME
    lame_cmd = [
        'lame',
        '-r',
        '-m', 'm',
        temp_file,
        mp3_file
    ]
    subprocess.run(lame_cmd, check=True)

    # Clean up the temporary raw audio file
    subprocess.run(['rm', temp_file], check=True)


def process_music_prompt(prompt, duration):
    # Fetch the command and generation pattern to generate MIDI
    c2m_command = fetch_c2m_tune(prompt)
    generation_pattern = fetch_generation_pattern(c2m_command, prompt)
    if not c2m_command or not generation_pattern:
        print("Failed to fetch or generate command or pattern.")
        return

    # Generate a unique timestamped MIDI filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    midi_filename = f"media/output_{timestamp}.mid"

    # Append the output file option to the command
    c2m_command += f" -o {midi_filename}"

    # Execute the command to generate MIDI file
    try:
        subprocess.run(c2m_command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute command: {e}")
        return

    # Convert the MIDI file to MP3
    mp3_filename = f"media/output_{timestamp}.mp3"
    convert_midi_to_mp3(midi_filename, mp3_filename)
    print(f"Generated MP3 file: {mp3_filename}")
    print(f"Used generation pattern: {generation_pattern}")

    # Encode the MP3 file to a base64 data URI
    with open(mp3_filename, "rb") as mp3_file:
        mp3_data = mp3_file.read()
        mp3_base64 = base64.b64encode(mp3_data).decode('utf-8')
        input_audio_url = f"data:audio/mpeg;base64,{mp3_base64}"

    # Call replicate API with the generated MP3 file
    input = {
        "prompt": generation_pattern,
        "duration": duration,
        "input_audio": input_audio_url
    }

    output = replicate.run(
        "nateraw/musicgen-songstarter-v0.2:020ac56a613f4494065e2e5544c7377788a8abcfbe645ecb8146634de0bc383e",
        input=input
    )
    print(output)

if __name__ == "__main__":
    # music_prompt = "happy triumphant tune for a tv news article with pictures of memes"
    music_prompt = "like a funky cocteau twins song but with a more upbeat and happy feel about a new AI model named llama3"
    duration = 10  # Duration in seconds
    process_music_prompt(music_prompt, duration)
