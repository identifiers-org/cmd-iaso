import gzip
import pickle
import re


def dump2pings(filepath, errors=None):
    pings = []

    with open(filepath, "rb") as raw:
        entry_points = [m.start() for m in re.finditer(b"\x1f\x8b", raw.read())]

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
