from .scanner import make_scanner
from .string import scanstring

from .generator.array import JSONArrayGenerator
from .generator.object import JSONObjectGenerator

from .lazy.value import LazyValue
from .lazy.array import LazyArray
from .lazy.object import LazyObject


class JSONLazyDecoder:
    _CONSTANTS = {
        b"null": None,
        b"true": True,
        b"false": False,
        b"NaN": float("nan"),
        b"Infinity": float("inf"),
        b"-Infinity": float("-inf"),
    }

    def __init__(self, cache_depth=0, strict=True):
        self.cache_depth = max(0, cache_depth)

        self.parse_float = self.JSONFloat
        self.parse_int = self.JSONInt
        self.parse_constant = self.JSONConstant
        self.parse_string = self.JSONString
        self.parse_object = self.JSONObject
        self.parse_array = self.JSONArray

        self.strict = strict
        self.memo = {}

        self.scan_once = make_scanner(self)

    def lazy_decode(self, s, idx=0):
        try:
            res = self.scan_once(s, idx, 0)
        except StopIteration as err:
            raise JSONLazyDecodeError("Expecting value", err.value) from None
        return res

    def JSONFloat(self, s, start_and_end, depth):
        res = float(s)  # if depth <= self.cache_depth else None

        return LazyValue(res, start_and_end[0] - 1, start_and_end[1])

    def JSONInt(self, s, start_and_end, depth):
        res = int(s)  # if depth <= self.cache_depth else None

        return LazyValue(res, start_and_end[0] - 1, start_and_end[1])

    def JSONConstant(self, s, start_and_end, depth):
        res = self._CONSTANTS[
            s[start_and_end[0] : start_and_end[1] + 1]
        ]  # if depth <= self.cache_depth else None

        return LazyValue(res, start_and_end[0], start_and_end[1] + 1)

    def JSONString(self, s, end, depth, strict=True, **kwargs):
        res = scanstring(s, end, strict=strict, **kwargs)

        if depth > self.cache_depth:
            res[0] = None

        return LazyValue(res[0], end - 1, res[1])

    def JSONObject(self, s_and_end, strict, scan_once, depth, memo=None, **kwargs):
        generator = JSONObjectGenerator(
            s_and_end, strict, scan_once, depth, memo=memo, **kwargs
        )

        lazy = LazyObject(s_and_end[0], self, generator, s_and_end[1] - 1)

        if depth < self.cache_depth:
            return lazy.into()

        return lazy

    def JSONArray(self, s_and_end, scan_once, depth, **kwargs):
        generator = JSONArrayGenerator(s_and_end, scan_once, depth, **kwargs)

        lazy = LazyArray(s_and_end[0], self, generator, s_and_end[1] - 1)

        if depth < self.cache_depth:
            return lazy.into()

        return lazy
