import gzip
import pickle

from tqdm import tqdm

from athena import SharedFragmentTree

strings = [
    ("a", "b", "c", "d", "e"),
    ("a", "b", "c"),
    ("c", "d", "e"),
    ("b", "c")
]

tree = SharedFragmentTree(strings)

with open("dump.pickle", "wb") as file:
    pickle.dump(tree, file)

with open("dump.pickle", "rb") as file:
    tree = pickle.load(file)

with gzip.open("dump.gz", "wb") as file:
    pickle.dump(tree, file)

with gzip.open("dump.gz", "rb") as file:
    tree = pickle.load(file)

print(tree.extract_longest_common_non_overlapping_substrings({0}, {1, 2, 3}, debug=False))

print(tree.extract_combination_of_all_common_fragments())

with tqdm(total=len(tree)) as progress:
    print(tree.extract_all_shared_fragments_for_all_strings_parallel(progress=progress.update))

with tqdm(total=len(tree)) as progress:
    print(tree.extract_all_shared_fragments_for_all_strings_sequential(progress=progress.update))
