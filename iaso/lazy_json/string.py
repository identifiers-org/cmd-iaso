from .error import JSONLazyDecodeError
from .re import BACKSLASH, STRINGCHUNK


def _decode_uXXXX(s, pos):
    esc = s[pos + 1 : pos + 5]
    if len(esc) == 4 and esc[1] not in b"xX":
        try:
            return int(esc, 16)
        except ValueError:
            pass
    msg = "Invalid \\uXXXX escape"
    raise JSONLazyDecodeError(msg, pos)


def scanstring(s, end, strict=True, _b=BACKSLASH, _m=STRINGCHUNK.match):
    """Scan the string s for a JSON string. End is the index of the
    character in s after the quote that started the JSON string.
    Unescapes all valid JSON string escape sequences and raises ValueError
    on attempt to decode an invalid string. If strict is False then literal
    control characters are allowed in the string.
    Returns a tuple of the decoded string and the index of the character in s
    after the end quote."""
    chunks = []
    _append = chunks.append
    begin = end - 1
    while 1:
        chunk = _m(s, end)
        if chunk is None:
            raise JSONLazyDecodeError("Unterminated string starting at", begin)
        end = chunk.end()
        content, terminator = chunk.groups()
        # Content is contains zero or more unescaped string characters
        if content:
            _append(content)
        # Terminator is the end of string, a literal control character,
        # or a backslash denoting that an escape sequence follows
        if terminator == b'"':
            break
        elif terminator != b"\\":
            if strict:
                # msg = "Invalid control character %r at" % (terminator,)
                msg = "Invalid control character {0!r} at".format(terminator)
                raise JSONLazyDecodeError(msg, end)
            else:
                _append(terminator)
                continue
        try:
            esc = s[end]
        except IndexError:
            raise JSONLazyDecodeError(
                "Unterminated string starting at", begin
            ) from None
        # If not a unicode escape sequence, must be in the lookup table
        if esc != b"u":
            try:
                char = _b[esc]
            except KeyError:
                msg = "Invalid \\escape: {0!r}".format(esc)
                raise JSONLazyDecodeError(msg, end)
            end += 1
        else:
            uni = _decode_uXXXX(s, end)
            end += 5
            if 0xD800 <= uni <= 0xDBFF and s[end : end + 2] == b"\\u":
                uni2 = _decode_uXXXX(s, end + 1)
                if 0xDC00 <= uni2 <= 0xDFFF:
                    uni = 0x10000 + (((uni - 0xD800) << 10) | (uni2 - 0xDC00))
                    end += 6
            char = chr(uni)
        _append(char)
    return b"".join(chunks).decode("utf-8"), end
