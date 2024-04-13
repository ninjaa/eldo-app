from moviepy.editor import TextClip


def generate_subtitle_clips(narration, total_duration, top_spacing, words_per_phrase=3):
    words = narration.split()
    phrases = [' '.join(words[i:i+words_per_phrase])
               for i in range(0, len(words), words_per_phrase)]
    total_word_count = len(words)
    clips = []
    current_time = 0

    for phrase in phrases:
        phrase_word_count = len(phrase.split())
        # Calculate the duration for the phrase based on its proportion of the total word count
        phrase_duration = (phrase_word_count /
                           total_word_count) * total_duration
        # Create a TextClip for the phrase
        subtitle_clip = TextClip(phrase, fontsize=70, color='white', font='Lato',
                                 align='South', stroke_color='black', stroke_width=3)

        subtitle_clip = subtitle_clip.set_start(current_time).set_duration(
            phrase_duration
        ).set_position(
            ('center', top_spacing)
        )
        clips.append(subtitle_clip)
        current_time += phrase_duration  # Update the current time for the next phrase

    return clips
