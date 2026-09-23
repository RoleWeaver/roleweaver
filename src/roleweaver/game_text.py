"""Prepare typographic punctuation for legacy Neverwinter Nights chat inputs.

Keep letters in the selected language intact. Only punctuation known to turn
into replacement characters in the game is converted to plain equivalents.
"""

_GAME_PUNCTUATION = str.maketrans(
    {
        "\u2018": "'",  # left single quotation mark
        "\u2019": "'",  # right single quotation mark / apostrophe
        "\u201a": "'",  # single low-9 quotation mark
        "\u201b": "'",  # single high-reversed-9 quotation mark
        "\u02bc": "'",  # modifier letter apostrophe
        "\u201c": '"',  # left double quotation mark
        "\u201d": '"',  # right double quotation mark
        "\u201e": '"',  # double low-9 quotation mark
        "\u201f": '"',  # double high-reversed-9 quotation mark
        "\u2010": "-",  # hyphen
        "\u2011": "-",  # non-breaking hyphen
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2015": "-",  # horizontal bar
        "\u2026": "...",  # ellipsis
        "\u00a0": " ",  # non-breaking space
        "\u202f": " ",  # narrow non-breaking space
    }
)


def normalize_game_punctuation(text: str) -> str:
    """Replace game-incompatible punctuation without changing words or lines."""

    return str(text).translate(_GAME_PUNCTUATION)
