from ..error import JSONLazyDecodeError
from ..re import WHITESPACE, WHITESPACE_STR


def JSONArrayGenerator(
    s_and_end, scan_once, depth, _w=WHITESPACE.match, _ws=WHITESPACE_STR
):
    s, end = s_and_end
    values = []
    nextchar = s[end : end + 1]
    if nextchar in _ws:
        end = _w(s, end + 1).end()
        nextchar = s[end : end + 1]
    # Look-ahead for trivial empty array
    if nextchar == b"]":
        return values, end + 1
    _append = values.append
    while True:
        try:
            res = scan_once(s, end, depth + 1)
        except StopIteration as err:
            raise JSONLazyDecodeError("Expecting value", err.value) from None
        value = res
        yield value
        end = res.end
        _append(value)
        nextchar = s[end : end + 1]
        if nextchar in _ws:
            end = _w(s, end + 1).end()
            nextchar = s[end : end + 1]
        end += 1
        if nextchar == b"]":
            break
        elif nextchar != b",":
            raise JSONLazyDecodeError("Expecting ',' delimiter", end - 1)
        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end + 1).end()
        except IndexError:
            pass

    return values, end
