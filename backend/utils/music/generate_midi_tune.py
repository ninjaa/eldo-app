import subprocess
import datetime
import mido
import random


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


if __name__ == "__main__":
    midi_filename = generate_midi_tune('happy', 120, 10)
    convert_midi_to_mp3(midi_filename, 'happy_tune.mp3')

    midi_filename = generate_midi_tune('sad', 80, 10)
    convert_midi_to_mp3(midi_filename, 'sad_tune.mp3')

    midi_filename = generate_midi_tune('neutral', 100, 10)
    convert_midi_to_mp3(midi_filename, 'neutral_tune.mp3')
