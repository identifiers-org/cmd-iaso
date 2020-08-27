import re

FLAGS = re.VERBOSE | re.MULTILINE | re.DOTALL

WHITESPACE = re.compile(b"[ \\t\\n\\r]*", FLAGS)
WHITESPACE_STR = b" \t\n\r"

STRINGCHUNK = re.compile(b'(.*?)(["\\\\\\x00-\\x1f])', FLAGS)
BACKSLASH = {
    b'"': b'"',
    b"\\": b"\\",
    b"/": b"/",
    b"b": b"\b",
    b"f": b"\f",
    b"n": b"\n",
    b"r": b"\r",
    b"t": b"\t",
}

NUMBER_RE = re.compile(b"(-?(?:0|[1-9]\\d*))(\\.\\d+)?([eE][-+]?\\d+)?", FLAGS)
