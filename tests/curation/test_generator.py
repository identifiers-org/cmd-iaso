from iaso.curation.generator import (
    CurationDirection,
    CurationEntry,
    curation_entry_generator,
)


def collectFromGenerator(entries, validators, directions, initial=0):
    entries = curation_entry_generator(entries, validators)
    next(entries)
    entries.send(initial)

    output = []

    for direction in directions:
        entry = entries.send(direction)

        if entry == CurationDirection.FINISH:
            break

        output.append(entry)
        next(entries)

    return output


class TestCurationEntryGenerator:
    def test_curation_directions_are_correct(self):
        assert CurationDirection.RELOAD == 0
        assert CurationDirection.FORWARD == +1
        assert CurationDirection.BACKWARD == -1

    def test_curation_finish_direction_is_unique(self):
        assert (
            len(
                {
                    CurationDirection.RELOAD,
                    CurationDirection.FORWARD,
                    CurationDirection.BACKWARD,
                    CurationDirection.FINISH,
                }
            )
            == 4
        )

    def test_generator_produces_all_items_with_passthrough_validator(self):
        for entry, expect in zip(
            collectFromGenerator(
                list(range(10)), [lambda _: None], [CurationDirection.FORWARD] * 10
            ),
            range(10),
        ):
            assert entry.entry == expect
            assert entry.validations == [None]

    def test_generator_produces_no_entries_from_nothing(self):
        assert (
            collectFromGenerator([], [lambda _: None], [CurationDirection.FORWARD] * 10)
            == []
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
            assert entry.entry == expect
            assert entry.validations == [None]

    def test_generator_filters_out_forbidden_entries(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3],
                [(lambda _: None), (lambda e: False if e == 2 else None)],
                [CurationDirection.FORWARD] * 3,
            ),
            [1, 3],
        ):
            assert entry.entry == expect
            assert entry.validations == [None, None]

    def test_generator_returns_error_reporting_validators(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3],
                [(lambda e: e), (lambda e: e != 2)],
                [CurationDirection.FORWARD] * 3,
            ),
            [1, 3],
        ):
            assert entry.entry == expect
            assert entry.validations == [expect]

    def test_generator_entries_wraps_around(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.FORWARD] * 6
            ),
            [1, 2, 3, 1, 2, 3],
        ):
            assert entry.entry == expect
            assert entry.validations == [None]

    def test_generator_backward_direction_produces_reverse_entries(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.BACKWARD] * 6
            ),
            [1, 3, 2, 1, 3, 2],
        ):
            assert entry.entry == expect
            assert entry.validations == [None]

    def test_generator_reload_produces_same_item(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.RELOAD] * 6
            ),
            [1] * 6,
        ):
            assert entry.entry == expect
            assert entry.validations == [None]

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
            assert entry.entry == expect
            assert entry.validations == [None]

    def test_generator_finishes_on_unknown_direction(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3],
                [lambda _: None],
                [CurationDirection.FORWARD, CurationDirection.FORWARD, 42],
            ),
            [1, 2],
        ):
            assert entry.entry == expect
            assert entry.validations == [None]

    def test_generator_position_is_correct_forward(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.FORWARD] * 6
            ),
            [0, 1, 2, 0, 1, 2],
        ):
            assert entry.position == expect

    def test_generator_position_is_correct_backward_eventually(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.BACKWARD] * 9
            ),
            [0, 1, 1, 0, 2, 1, 0, 2, 1],
        ):
            assert entry.position == expect

    def test_generator_total_converges_to_valid_entries_amount(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.FORWARD] * 6
            ),
            ["1+", "2+", "3", "3", "3", "3"],
        ):
            assert entry.total == expect

    def test_generator_can_start_from_arbitrary_position(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3, 4, 5], [lambda _: None], [CurationDirection.FORWARD] * 3, 2
            ),
            [3, 4, 5],
        ):
            assert entry.entry == expect

    def test_generator_out_of_bounds_start_position_wraps_around(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.FORWARD], 7
            ),
            [2],
        ):
            assert entry.entry == expect

    def test_generator_entry_index_returns_internal_index(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.FORWARD] * 5, 1
            ),
            [1, 2, 0, 1, 2],
        ):
            assert entry.index == expect

    def test_generator_entry_visited_converges_to_full_indices_set(self):
        for entry, expect in zip(
            collectFromGenerator(
                [1, 2, 3], [lambda _: None], [CurationDirection.FORWARD] * 5, 1
            ),
            [set([1]), set([1, 2]), set([0, 1, 2]), set([0, 1, 2]), set([0, 1, 2])],
        ):
            assert entry.visited == expect
