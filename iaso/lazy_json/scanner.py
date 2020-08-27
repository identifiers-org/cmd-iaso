from .re import NUMBER_RE


def make_scanner(context):
    parse_object = context.parse_object
    parse_array = context.parse_array
    parse_string = context.parse_string
    match_number = NUMBER_RE.match
    strict = context.strict
    parse_float = context.parse_float
    parse_int = context.parse_int
    parse_constant = context.parse_constant
    memo = context.memo

    def _scan_once(string, idx, depth):
        try:
            nextchar = string[idx : idx + 1]
        except IndexError:
            raise StopIteration(idx) from None

        if nextchar == b'"':
            return parse_string(string, idx + 1, depth, strict)
        elif nextchar == b"{":
            return parse_object((string, idx + 1), strict, _scan_once, depth, memo)
        elif nextchar == b"[":
            return parse_array((string, idx + 1), _scan_once, depth)
        elif nextchar == b"n" and string[idx : idx + 4] == b"null":
            return parse_constant(string, (idx, idx + 3), depth)
        elif nextchar == b"t" and string[idx : idx + 4] == b"true":
            return parse_constant(string, (idx, idx + 3), depth)
        elif nextchar == b"f" and string[idx : idx + 5] == b"false":
            return parse_constant(string, (idx, idx + 4), depth)

        m = match_number(string, idx)

        if m is not None:
            integer, frac, exp = m.groups()
            if frac or exp:
                return parse_float(
                    integer + (frac or b"") + (exp or b""), (idx + 1, m.end()), depth
                )
            else:
                return parse_int(integer, (idx + 1, m.end()), depth)
        elif nextchar == b"N" and string[idx : idx + 3] == b"NaN":
            return parse_constant(string, (idx, idx + 2), depth)
        elif nextchar == b"I" and string[idx : idx + 8] == b"Infinity":
            return parse_constant(string, (idx, idx + 7), depth)
        elif nextchar == b"-" and string[idx : idx + 9] == b"-Infinity":
            return parse_constant(string, (idx, idx + 8), depth)
        else:
            raise StopIteration(idx)

    def scan_once(string, idx, depth):
        try:
            return _scan_once(string, idx, depth)
        finally:
            memo.clear()

    return scan_once
