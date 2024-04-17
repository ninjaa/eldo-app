from moviepy.editor import TextClip


def fit_text_in_line(text, max_chars, font_size):
    lines = []
    while text:
        line, text = text[:max_chars], text[max_chars:]
        lines.append(line)
    return lines


def generate_subtitle_clips(narration, total_duration, max_text_width, top_spacing, font_size=30, line_spacing=5, words_per_phrase=3):
    words = narration.split()
    phrases = [' '.join(words[i:i+words_per_phrase])
               for i in range(0, len(words), words_per_phrase)]
    total_word_count = len(words)
    clips = []
    current_time = 0

    for phrase in phrases:
        phrase_word_count = len(phrase.split())
        phrase_duration = (phrase_word_count /
                           total_word_count) * total_duration

        max_chars = int((max_text_width / font_size) * 1.6)
        phrase_lines = fit_text_in_line(phrase, max_chars, font_size)

        phrase_height = font_size * \
            (len(phrase_lines) + (len(phrase_lines) - 1) * line_spacing / font_size)

        subtitle_clip = TextClip(
            '\n'.join(phrase_lines),
            fontsize=font_size,
            color='white',
            font="Amiri-Bold",
            align='South',
            stroke_color='black',
            size=(max_text_width, phrase_height),
            stroke_width=3
        )

        subtitle_position = ((1080 - max_text_width) / 2, top_spacing)
        subtitle_clip = subtitle_clip.set_start(current_time).set_duration(
            phrase_duration).set_position(subtitle_position)
        clips.append(subtitle_clip)

        current_time += phrase_duration

    return clips
