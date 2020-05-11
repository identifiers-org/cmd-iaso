import unittest

from iaso.curation.generator import (
    CurationDirection,
    CurationEntry,
    curation_entry_generator,
)


def collectFromGenerator(entries, validators, directions):
    entries = curation_entry_generator(entries, validators)
    next(entries)

    output = []

    for direction in directions:
        entry = entries.send(direction)

        if entry == CurationDirection.FINISH:
            break

        output.append(entry)
        next(entries)

    return output


class TestCurationEntryGenerator(unittest.TestCase):
    def test_curation_directions_are_correct(self):
        self.assertEqual(CurationDirection.RELOAD, 0)
        self.assertEqual(CurationDirection.FORWARD, +1)
        self.assertEqual(CurationDirection.BACKWARD, -1)

    def test_curation_finish_direction_is_unique(self):
        self.assertEqual(
            len(
                {
                    CurationDirection.RELOAD,
                    CurationDirection.FORWARD,
                    CurationDirection.BACKWARD,
                    CurationDirection.FINISH,
                }
            ),
            4,
        )

    def test_generator_produces_all_items_with_passthrough_validator(self):
        for entry, expect in zip(
            collectFromGenerator(
                list(range(10)), [lambda _: None], [CurationDirection.FORWARD] * 10
            ),
            range(10),
        ):
            self.assertEqual(entry.entry, expect)
            self.assertEqual(entry.validations, [None])

    def test_generator_produces_no_entries_from_nothing(self):
        self.assertEqual(
            collectFromGenerator(
                [], [lambda _: None], [CurationDirection.FORWARD] * 10
            ),
            [],
        )

    def test_generator_filters_out_valid_entries(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3],
                [lambda e: True if e == 2 else None],
                [CurationDirection.FORWARD] * 3,
            ),
            [1, 3],
        ):
            self.assertEqual(entry.entry, expect)
            self.assertEqual(entry.validations, [None])

    def test_generator_filters_out_forbidden_entries(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3],
                [(lambda _: None), (lambda e: False if e == 2 else None)],
                [CurationDirection.FORWARD] * 3,
            ),
            [1, 3],
        ):
            self.assertEqual(entry.entry, expect)
            self.assertEqual(entry.validations, [None, None])

    def test_generator_returns_error_reporting_validators(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3],
                [(lambda e: e), (lambda e: e != 2)],
                [CurationDirection.FORWARD] * 3,
            ),
            [1, 3],
        ):
            self.assertEqual(entry.entry, expect)
            self.assertEqual(entry.validations, [expect])

    def test_generator_entries_wraps_around(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.FORWARD] * 6
            ),
            [1, 2, 3, 1, 2, 3],
        ):
            self.assertEqual(entry.entry, expect)
            self.assertEqual(entry.validations, [None])

    def test_generator_backward_direction_produces_reverse_entries(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.BACKWARD] * 6
            ),
            [1, 3, 2, 1, 3, 2],
        ):
            self.assertEqual(entry.entry, expect)
            self.assertEqual(entry.validations, [None])

    def test_generator_reload_produces_same_item(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.RELOAD] * 6
            ),
            [1] * 6,
        ):
            self.assertEqual(entry.entry, expect)
            self.assertEqual(entry.validations, [None])

    def test_generator_finishes_on_finish_direction(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3],
                [lambda _: None],
                [
                    CurationDirection.FORWARD,
                    CurationDirection.FORWARD,
                    CurationDirection.FINISH,
                ],
            ),
            [1, 2],
        ):
            self.assertEqual(entry.entry, expect)
            self.assertEqual(entry.validations, [None])

    def test_generator_finishes_on_unknown_direction(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3],
                [lambda _: None],
                [CurationDirection.FORWARD, CurationDirection.FORWARD, 42],
            ),
            [1, 2],
        ):
            self.assertEqual(entry.entry, expect)
            self.assertEqual(entry.validations, [None])

    def test_generator_position_is_correct_forward(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.FORWARD] * 6
            ),
            [0, 1, 2, 0, 1, 2],
        ):
            self.assertEqual(entry.position, expect)

    def test_generator_position_is_correct_backward_eventually(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.BACKWARD] * 9
            ),
            [0, 1, 1, 0, 2, 1, 0, 2, 1],
        ):
            self.assertEqual(entry.position, expect)

    def test_generator_total_converges_to_valid_entries_amount(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.FORWARD] * 6
            ),
            ["1+", "2+", "3", "3", "3", "3"],
        ):
            self.assertEqual(entry.total, expect)
