from ..error import JSONLazyDecodeError
from ..re import WHITESPACE, WHITESPACE_STR
from ..string import scanstring


def JSONObjectGenerator(
    s_and_end,
    strict,
    scan_once,
    depth,
    memo=None,
    _w=WHITESPACE.match,
    _ws=WHITESPACE_STR,
):
    s, end = s_and_end
    pairs = []
    pairs_append = pairs.append
    # Backwards compatibility
    if memo is None:
        memo = {}
    memo_get = memo.setdefault
    # Use a slice to prevent IndexError from being raised, the following
    # check will raise a more specific ValueError if the string is empty
    nextchar = s[end : end + 1]
    # Normally we expect nextchar == '"'
    if nextchar != b'"':
        if nextchar in _ws:
            end = _w(s, end).end()
            nextchar = s[end : end + 1]
        # Trivial empty object
        if nextchar == b"}":
            return {}, end + 1
        elif nextchar != b'"':
            raise JSONLazyDecodeError(
                "Expecting property name enclosed in double quotes", end
            )
    end += 1
    while True:
        key, end = scanstring(s, end, strict)
        key = memo_get(key, key)
        # To skip some function call overhead we optimize the fast paths where
        # the JSON key separator is ": " or just ":".
        if s[end : end + 1] != b":":
            end = _w(s, end).end()
            if s[end : end + 1] != b":":
                raise JSONLazyDecodeError("Expecting ':' delimiter", end)
        end += 1

        try:
            if s[end] in _ws:
                end += 1
                if s[end] in _ws:
                    end = _w(s, end + 1).end()
        except IndexError:
            pass

        try:
            res = scan_once(s, end, depth + 1)
        except StopIteration as err:
            raise JSONLazyDecodeError("Expecting value", err.value) from None
        value = res
        yield (key, value)
        end = res.end
        pairs_append((key, value))
        try:
            nextchar = s[end : end + 1]
            if nextchar in _ws:
                end = _w(s, end + 1).end()
                nextchar = s[end : end + 1]
        except IndexError:
            nextchar = b""
        end += 1

        if nextchar == b"}":
            break
        elif nextchar != b",":
            raise JSONLazyDecodeError("Expecting ',' delimiter", end - 1)
        end = _w(s, end).end()
        nextchar = s[end : end + 1]
        end += 1
        if nextchar != b'"':
            raise JSONLazyDecodeError(
                "Expecting property name enclosed in double quotes", end - 1
            )
    return dict(pairs), end
