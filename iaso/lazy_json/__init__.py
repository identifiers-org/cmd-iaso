from .decoder import JSONLazyDecoder


def decode(bytearray, cache_depth=0, strict=True, idx=0):
    return JSONLazyDecoder(cache_depth=cache_depth, strict=strict).lazy_decode(
        bytearray, idx=idx
    )
