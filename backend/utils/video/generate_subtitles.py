from moviepy.editor import TextClip, ColorClip, CompositeVideoClip


def fit_text_in_line(text, max_chars, font_size):
    lines = []
    while text:
        if len(text) <= max_chars:
            lines.append(text)
            break
        split_at = text.rfind(' ', 0, max_chars)
        if split_at == -1:  # No spaces found, check for hyphenation
            # Attempt to hyphenate
            hyphenated = False
            for i in range(max_chars, 0, -1):
                if text[i-1] == '-':  # Found a hyphenation point
                    lines.append(text[:i])
                    text = text[i:]
                    hyphenated = True
                    break
            if not hyphenated:  # No hyphenation point found, force split
                split_at = max_chars
                lines.append(text[:split_at])
                text = text[split_at:]
            continue
        line, text = text[:split_at], text[split_at+1:]
        lines.append(line)
    return lines


def generate_subtitle_clips(narration, total_duration, max_text_width, top_spacing, font_size=30, screen_size=(1080, 1920), line_spacing=10, words_per_phrase=3):
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
            font="Helvetica-Bold",
            align='South',
            stroke_color='black',
            size=(max_text_width, phrase_height),
            stroke_width=2
        )

        subtitle_position = ('center', top_spacing)
        subtitle_clip = subtitle_clip.set_start(current_time).set_duration(
            phrase_duration).set_position(subtitle_position)

        # Create a background clip. Adjust color and opacity as needed.
        background_clip = ColorClip(size=(subtitle_clip.w, subtitle_clip.h + 10),
                                    color=(0, 0, 0))
        # Set the position of the background clip to match the subtitle clip
        background_clip = background_clip.set_start(current_time).set_duration(phrase_duration).set_position(
            ('center', top_spacing - 5))

        # To apply opacity, create a mask for the background clip using a ColorClip with the same size but in white and the desired opacity
        mask = ColorClip(size=(subtitle_clip.w, subtitle_clip.h + 10),
                         color=0.65, ismask=True)

        mask = mask.set_start(current_time).set_duration(phrase_duration).set_position(
            ('center', top_spacing - 5))

        # Set the mask to the background clip
        background_clip = background_clip.set_mask(mask).set_opacity(0.5)

        # Composite the subtitle clip over the background
        subtitle_clip_with_bg = CompositeVideoClip(
            [background_clip, subtitle_clip], size=screen_size)

        clips.append(subtitle_clip_with_bg)

        current_time += phrase_duration

    return clips
