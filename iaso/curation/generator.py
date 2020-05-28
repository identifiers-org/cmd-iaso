import bisect

from collections import namedtuple


class CurationDirection:
    RELOAD = 0
    FORWARD = +1
    BACKWARD = -1
    FINISH = None


CurationEntry = namedtuple(
    "CurationEntry", ("entry", "validations", "position", "total", "index", "visited")
)


def curation_entry_generator(entries, validators):
    wrap = len(entries)
    index = yield

    if wrap > 0:
        index = index % wrap

    indices = []
    non_indices = set()

    while True:
        # Pull a direction from the caller
        direction = yield

        # If we should finish, we finish
        if (
            direction != CurationDirection.RELOAD
            and direction != CurationDirection.FORWARD
            and direction != CurationDirection.BACKWARD
        ):
            yield CurationDirection.FINISH

            continue

        if wrap == 0:
            yield CurationDirection.FINISH

            continue

        start_index = index

        # Reloading before we have found an erroneous entry only works if we can
        # explore the remaining entries with a non-zero direction
        if direction == CurationDirection.RELOAD and len(indices) == 0:
            direction = CurationDirection.FORWARD

        # If we have already found an erroneous entry, we can skip to the next index immediately
        if len(indices) > 0:
            index = (index + direction) % wrap

        while True:
            validations = []

            for validator in validators:
                validation = validator(entries[index])

                # Validation of this entry is impossible -> continue with next index
                if isinstance(validation, bool) and validation == False:
                    validations.clear()

                    break

                # Everything ok
                if isinstance(validation, bool) and validation == True:
                    continue

                if isinstance(validation, list):
                    validations.extend(validation)
                else:
                    validations.append(validation)

            # We have found an erroneous entry if any validator submitted an objection
            if len(validations) > 0:
                break

            # Record valid entry for bookkeeping
            non_indices.add(index)

            index = (index + direction) % wrap

            # There are only valid entries
            if index == start_index and len(indices) == 0:
                yield CurationDirection.FINISH

                continue

        # Insert the erroneous entry index at the correct position
        pos = bisect.bisect_left(indices, index, 0, len(indices))

        if pos >= len(indices) or indices[pos] != index:
            indices.insert(pos, index)

        # Push an erroneous entry to the caller
        yield CurationEntry(
            entries[index],
            validations,
            pos,
            "{}+".format(len(indices))
            if (len(indices) + len(non_indices)) < wrap
            else str(len(indices)),
            index,
            non_indices.union(indices),
        )
