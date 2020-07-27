import pickle

from athena import SharedFragmentTree


def generate_tree():
    strings = [("a", "b", "c", "d", "e"), ("a", "b", "c"), ("c", "d", "e"), ("b", "c")]

    return SharedFragmentTree(strings)


class TestAthena:
    def test_tree_generation(self):
        generate_tree()

    def test_tree_len_builtin(self):
        assert len(generate_tree()) == 4

    def test_tree_str_builtin(self):
        str(generate_tree())

    def test_tree_size_getter(self):
        assert generate_tree().size == 17

    def test_tree_pickling(self):
        tree = generate_tree()

        dump = pickle.dumps(tree)
        dumped_tree = pickle.loads(dump)
        dumped_tree_dump = pickle.dumps(dumped_tree)

        assert dump == dumped_tree_dump
        assert str(tree) == str(dumped_tree)

    def test_lcnof(self):
        assert generate_tree().extract_longest_common_non_overlapping_fragments(
            {0}, {1, 2, 3}
        ) == [(["c", "d", "e"], 2), (["a", "b"], 0)]

    def test_acf_combination(self):
        assert generate_tree().extract_combination_of_all_common_fragments() == ["c"]

    def test_asffas_sequential(self):
        def progress():
            progress.counter += 1

        progress.counter = 0

        assert generate_tree().extract_all_shared_fragments_for_all_strings_sequential(
            threshold=None, progress=progress
        ) == [
            [["c", "d", "e"], ["a", "b"]],
            [["a", "b", "c"]],
            [["c", "d", "e"]],
            [["b", "c"]],
        ]

        assert progress.counter == 4

    def test_asffas_parallel(self):
        def progress():
            progress.counter += 1

        progress.counter = 0

        assert generate_tree().extract_all_shared_fragments_for_all_strings_parallel(
            threshold=None, progress=progress
        ) == [
            [["c", "d", "e"], ["a", "b"]],
            [["a", "b", "c"]],
            [["c", "d", "e"]],
            [["b", "c"]],
        ]

        assert progress.counter == 4
