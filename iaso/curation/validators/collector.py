from collections import defaultdict


class hashabledict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


class ErrorExampleCollector:
    def __init__(self, name):
        self.name = name
        self.collector = defaultdict(list)

    @staticmethod
    def make_hashable(obj):
        if isinstance(obj, list):
            return tuple(ErrorExampleCollector.make_hashable(child) for child in obj)

        if isinstance(obj, dict):
            return hashabledict(
                {
                    key: ErrorExampleCollector.make_hashable(value)
                    for key, value in obj.items()
                }
            )

        return obj

    def add(self, info, compid):
        self.collector[ErrorExampleCollector.make_hashable(info)].append(compid)

    def __len__(self):
        return len(self.collector)

    def result(self):
        return [
            {
                self.name: info,
                "Example Compact Identifiers": [
                    f"[{compid}](https://identifiers.org/resolve?query={compid})"
                    for compid in set(compids)
                ],
            }
            for info, compids in self.collector.items()
        ]
