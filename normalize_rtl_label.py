from qgis.core import qgsfunction
import unicodedata


@qgsfunction(args=1, group='Custom')
def normalize_rtl_label(values, feature, parent):
    """
    normalize_rtl_label(<string>) → string
    Reverses characters in each RTL part of the input string,
    reorders adjacent RTL segments to ensure logical visual order,
    and corrects bracket directions in RTL text.
    """
    val = values[0]
    if val is None:
        return None
    if not isinstance(val, str):
        raise ValueError('normalize_rtl_label: input is not a string')

    # Mapping: [isolated, final, initial, medial]
    # Include Kurdish/Persian and ensure dotless forms for Kurdish E (ێ)
    arabic_forms = {
        '\u0621': ['\uFE80', '\uFE80', '\uFE80', '\uFE80'],  # Hamza
        '\u0622': ['\uFE81', '\uFE82', '\uFE81', '\uFE82'],  # Alef with Madda
        '\u0627': ['\uFE8D', '\uFE8E', '\uFE8D', '\uFE8E'],  # Alef
        '\u0628': ['\uFE8F', '\uFE90', '\uFE91', '\uFE92'],  # Beh
        '\u062A': ['\uFE95', '\uFE96', '\uFE97', '\uFE98'],  # Teh
        '\u062C': ['\uFE9D', '\uFE9E', '\uFE9F', '\uFEA0'],  # Jeem
        '\u062D': ['\uFEA1', '\uFEA2', '\uFEA3', '\uFEA4'],  # Hah
        '\u062E': ['\uFEA5', '\uFEA6', '\uFEA7', '\uFEA8'],  # Khah
        '\u062F': ['\uFEA9', '\uFEAA', '\uFEA9', '\uFEAA'],  # Dal
        '\u0630': ['\uFEAB', '\uFEAC', '\uFEAB', '\uFEAC'],  # Thal
        '\u0631': ['\uFEAD', '\uFEAE', '\uFEAD', '\uFEAE'],  # Reh
        '\u0632': ['\uFEAF', '\uFEB0', '\uFEAF', '\uFEB0'],  # Zain
        '\u0633': ['\uFEB1', '\uFEB2', '\uFEB3', '\uFEB4'],  # Seen
        '\u0634': ['\uFEB5', '\uFEB6', '\uFEB7', '\uFEB8'],  # Sheen
        '\u0635': ['\uFEB9', '\uFEBA', '\uFEBB', '\uFEBC'],  # Sad
        '\u0636': ['\uFEBD', '\uFEBE', '\uFEBF', '\uFEC0'],  # Dad
        '\u0637': ['\uFEC1', '\uFEC2', '\uFEC3', '\uFEC4'],  # Tah
        '\u0638': ['\uFEC5', '\uFEC6', '\uFEC7', '\uFEC8'],  # Zah
        '\u0639': ['\uFEC9', '\uFECA', '\uFECB', '\uFECC'],  # Ain
        '\u063A': ['\uFECD', '\uFECE', '\uFECF', '\uFED0'],  # Ghain
        '\u0641': ['\uFED1', '\uFED2', '\uFED3', '\uFED4'],  # Feh
        '\u0642': ['\uFED5', '\uFED6', '\uFED7', '\uFED8'],  # Qaf
        '\u0643': ['\uFED9', '\uFEDA', '\uFEDB', '\uFEDC'],  # Kaf
        '\u0644': ['\uFEDD', '\uFEDE', '\uFEDF', '\uFEE0'],  # Lam
        '\u0645': ['\uFEE1', '\uFEE2', '\uFEE3', '\uFEE4'],  # Meem
        '\u0646': ['\uFEE5', '\uFEE6', '\uFEE7', '\uFEE8'],  # Noon
        '\u0647': ['\uFEE9', '\uFEEA', '\uFEEB', '\uFEEC'],  # Heh
        '\u0648': ['\uFEED', '\uFEEE', '\uFEED', '\uFEEE'],  # Waw
        '\u064A': ['\uFEF1', '\uFEF2', '\uFEF3', '\uFEF4'],  # Yeh (Arabic)
        '\u067E': ['\uFB56', '\uFB57', '\uFB58', '\uFB59'],  # Peh (پ)
        '\u0686': ['\uFB7A', '\uFB7B', '\uFB7C', '\uFB7D'],  # Tcheh (چ)
        # Kurdish R (ڕ): Right-connecting only
        '\u0695': ['\uFB8C', '\uFB8D', '\uFB8C', '\uFB8D'],

        # Kurdish Lam (ڵ): Full connectivity with the small 'v' diacritic
        '\u06B5': ['\uFBB2', '\uFBB3', '\uFBB4', '\uFBB5'],

        # Kurdish O (ۆ): Right-connecting only
        '\u06C6': ['\uFB84', '\uFB85', '\uFB84', '\uFB85'],

        # Kurdish E (ێ): Using dotless Farsi Yeh presentation forms.
        # This is the ONLY way to force dotless initial/medial shapes
        # for curved labels in most QGIS-compatible fonts.
        '\u06CE': ['\uFBFC', '\uFBFD', '\uFBFE', '\uFBFF'],

        # Kurdish Ae (ە):
        # Right-connecting only (represented by visual Heh forms)
        '\u06D5': ['\uFEE9', '\uFEEA', '\uFEE9', '\uFEEA'],

        # Farsi/Kurdish Yeh (ی): Dotless in all positions
        '\u06CC': ['\uFBFC', '\uFBFD', '\uFBFE', '\uFBFF'],
    }

    # Letters that only connect to the RIGHT (previous character)
    right_only = {
        '\u0621', '\u0622', '\u0623', '\u0624', '\u0625', '\u0627',
        '\u062F', '\u0630', '\u0631', '\u0632', '\u0648', '\u0649',
        '\u0695', '\u06C6', '\u06D5'
    }

    def reshape_arabic(text):
        """Convert Arabic text to presentation forms based on position"""
        result = []
        chars = list(text)
        for i, ch in enumerate(chars):
            if ch not in arabic_forms:
                result.append(ch)
                continue

            # Connection logic matching your successful terminal test
            prev_char = chars[i - 1] if i > 0 else None
            next_char = chars[i + 1] if i < len(chars) - 1 else None
            prev_connected = prev_char in arabic_forms
            next_connected = next_char in arabic_forms
            conn_prev = prev_connected and prev_char not in right_only
            conn_next = next_connected and ch not in right_only

            if conn_prev and conn_next:
                idx = 3  # medial
            elif conn_prev:
                idx = 1  # final
            elif conn_next:
                idx = 2  # initial
            else:
                idx = 0  # isolated

            result.append(arabic_forms[ch][idx])
        return ''.join(result)

    # Keep the rest of your directional run and
    # reversing logic from normalize_rtl_label.py
    rtl_punctuation_map = str.maketrans({
        '(': ')',
        ')': '(',
        '[': ']',
        ']': '[',
        '{': '}',
        '}': '{',
        '<': '>',
        '>': '<'
    })
    runs = []
    current_dir = None
    current_text = ''
    for ch in val:
        bidi = unicodedata.bidirectional(ch)
        dir_flag = 'Neutral'
        if bidi in ('R', 'AL', 'RLE', 'RLO'):
            dir_flag = 'RTL'
        elif bidi in ('L', 'LRE', 'LRO'):
            dir_flag = 'LTR'
        if dir_flag != current_dir:
            if current_text:
                runs.append((current_text, current_dir))
            current_text = ch
            current_dir = dir_flag
        else:
            current_text += ch
    if current_text:
        runs.append((current_text, current_dir))

    def is_arabic_char(ch):
        return any([
            '\u0600' <= ch <= '\u06FF',
            '\u0750' <= ch <= '\u077F',
            '\u08A0' <= ch <= '\u08FF'
        ])

    reversed_runs = []
    for text, direction in runs:
        if direction == 'RTL':
            has_arabic = any(is_arabic_char(ch) for ch in text)
            if has_arabic:
                adjusted_text = reshape_arabic(text)[::-1].translate(
                    rtl_punctuation_map
                )
            else:
                adjusted_text = text[::-1].translate(rtl_punctuation_map)
            reversed_runs.append((adjusted_text, direction))
        else:
            reversed_runs.append((text, direction))

    final_runs = []
    temp_group = []

    def flush_group():
        if temp_group:
            final_runs.extend(reversed(temp_group))
            temp_group.clear()
    for text, direction in reversed_runs:
        if direction in ('RTL', 'Neutral'):
            temp_group.append((text, direction))
        else:
            flush_group()
            final_runs.append((text, direction))
    flush_group()

    return ''.join(text for text, _ in final_runs).translate(
        rtl_punctuation_map)
