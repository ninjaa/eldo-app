from moviepy.editor import TextClip


def generate_subtitle_clips(narration, total_duration, max_text_width, top_spacing, words_per_phrase=3):
    words = narration.split()
    phrases = [' '.join(words[i:i+words_per_phrase])
               for i in range(0, len(words), words_per_phrase)]
    total_word_count = len(words)
    clips = []
    current_time = 0

    min_font_size = 30  # Minimum font size to ensure readability
    max_font_size = 40  # Maximum font size for aesthetic purposes
    font_step_size = (max_font_size - min_font_size) / (words_per_phrase - 1)

    for phrase in phrases:
        phrase_word_count = len(phrase.split())
        # Calculate the duration for the phrase based on its proportion of the total word count
        phrase_duration = (phrase_word_count /
                           total_word_count) * total_duration
        adjusted_font_size = max_font_size - \
            font_step_size * (phrase_word_count - 1)
        adjusted_font_size = max(min_font_size, min(
            max_font_size, adjusted_font_size))

        # Create a TextClip for the phrase
        subtitle_clip = TextClip(
            phrase,
            fontsize=adjusted_font_size,
            color='white',
            font='Lato',
            align='South',
            stroke_color='black',
            size=(max_text_width, None),
            stroke_width=3
        )

        subtitle_clip = subtitle_clip.set_start(current_time).set_duration(
            phrase_duration
        ).set_position(
            ('center', top_spacing)
        )
        clips.append(subtitle_clip)
        current_time += phrase_duration  # Update the current time for the next phrase

    return clips
