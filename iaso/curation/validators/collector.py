from collections import Counter, defaultdict


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

    def add(self, info, compid, random):
        self.collector[ErrorExampleCollector.make_hashable(info)].append(
            (compid, random)
        )

    def __len__(self):
        return len(self.collector)

    def result_compid_list(self, total_compids):
        return [
            {
                self.name: info,
                "Example Compact Identifiers": [
                    f"{count}/{total_compids[compid]} x [{compid}](https://identifiers.org/resolve?query={compid}) "
                    + f"({'' if random else 'non-'}random)"
                    for (compid, random), count in Counter(compids).most_common()
                ],
            }
            for info, compids in self.collector.items()
        ]

    def result_compid_dict(self, total_compids):
        return [
            {
                self.name: info,
                "Example Compact Identifiers": {
                    (
                        f"{count}/{total_compids[compid]} x [{compid}](https://identifiers.org/resolve?query={compid}) "
                        + f"({'' if random else 'non-'}random)"
                    ): compid
                    for (compid, random), count in Counter(compids).most_common()
                },
            }
            for info, compids in self.collector.items()
        ]

    def result(self, total_compids):
        return self.result_compid_list(total_compids)
