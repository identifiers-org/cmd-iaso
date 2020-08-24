import gzip
import mmap
import pickle
import re


def dump2pings(filepath, errors=None):
    pings = []

    with open(filepath, "r+b") as raw:
        with mmap.mmap(raw.fileno(), 0) as raw:
            entry_points = [m.start() for m in re.finditer(b"\x1f\x8b", raw)]

            for entry_point in entry_points:
                raw.seek(entry_point)

                try:
                    with gzip.GzipFile(fileobj=raw, mode="rb") as file:
                        pings.append(pickle.load(file))
                except OSError:
                    pass
                except Exception as err:
                    if errors is not None:
                        errors[filepath].append(err)

    return pings
