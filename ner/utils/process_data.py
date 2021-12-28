import re


def normalize_text(raw_description: str, annotator) -> str:
    # remove strip_emoji
    def strip_emoji(text):
        RE_EMOJI = re.compile(u'([\U00002600-\U000027BF])|([\U0001f300-\U0001f64F])|([\U0001f680-\U0001f6FF])')
        return RE_EMOJI.sub(r'', text)

    def normalize_line(line: str) -> str:
        line = line.strip(' ')
        line = line.strip(' -+')

        return line

    def segment_word(line: str, annotator) -> str:
        segmented_list = annotator.tokenize(line)
        segmented_line = ''
        for sen in segmented_list:
            segmented_line += ' '.join(sen)
            segmented_line += ' '

        segmented_line = segmented_line.replace(' .', '.')
        segmented_line = segmented_line.replace(' ,', ',')
        segmented_line = segmented_line.replace(' / ', '/')
        segmented_line = segmented_line.replace(' :', ':')

        return segmented_line

    raw_text: str = strip_emoji(raw_description)
    raw_text = raw_text.replace('\r', '')
    raw_text = raw_text.replace('"', '')

    lines = raw_text.split('\n')
    lines = [normalize_line(line) for line in lines]

    segmented_lines = []
    for line in lines:
        if len(line) and line != '':
            segmented_lines.append(segment_word(line, annotator=annotator))
        else:
            segmented_lines.append(line)

    flag = False
    cleand_lines = []

    for i in range(len(segmented_lines) - 1):
        line1 = segmented_lines[i]
        line2 = segmented_lines[i + 1]

        if line1 == line2 and line1 == '':
            flag = True
            continue
        else:
            flag = False

        if not flag:
            cleand_lines.append(line1)

    cleand_lines.append(segmented_lines[-1])
    cleaned_text = '\n'.join(cleand_lines)

    return cleaned_text