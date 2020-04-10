import dragonfly


def double_text_punc_dict():
    return {
        # "quotes":                            "\"\"",
        # "thin quotes":                         "''",
        # "tickris":                             "``",
        # "prekris":                             "()",
        "thin quotes":                                "[]",
        # "curly":                               "{}",
        # "angle":                               "<>",
    }


def _inv_dtpb():
    return {v: k for k, v in double_text_punc_dict().items()}


def text_punc_dict():
    # Insurers comma is recognized consistently with DNS/Natlink and
    # if/else statement workaround engines that do not expect punctuation symbol as a command
    if (dragonfly.engines.get_engine()._name == 'natlink'):
        comma = "(comma | ,)"
    else:
        comma = "comma"

    _id = _inv_dtpb()
    return {
    # no shift required
    'tick|back tick|backtick': '`',
    'minus|dash|hyphen': '-',
    'equals|equal': '=',
    'comma': ',',
    'dot|period': '.',
    'slash|forward slash': '/',
    'semicolon|semi': ';',
    'quote|single quote|apostrophe': '\'',
    'square|open square|left square|bracket|open bracket|left bracket': '[',
    'close square|right square|close bracket|right bracket': ']',
    'backslash': '\\',

    # shift required
    'tilde': '~',
    'underscore|under score|under': '_',
    'plus': '+',
    'angle|open angle|left angle|less than': '<',
    'close angle|right angle|greater than': '>',
    'question|question mark': '?',
    'colon': ':',
    'double quote|double quotes': '"',
    'brace|open brace|left brace|curly|open curly|left curly': '{',
    'close brace|right brace|close curly|right curly': '}',
    'pipe|bar': '|',

    # above numbers
    'bang|exclamation|exclamation point': '!',
    'at sign': '@',
    'pound|pound sign|hash|hash sign|hashtag|hash tag|number sign': '#',
    'dollar|dollar sign': '$',
    'percent|percent sign': '%',
    'caret': '^',
    'ampersand': '&',
    'star|asterisk': '*',
    'paren|open paren|left paren': '(',
    'close paren|right paren': ')',

    }
