use super::SharedFragmentTree;

fn generate_tree() -> SharedFragmentTree {
    SharedFragmentTree::new(vec![
        vec![
            "a".to_owned(),
            "b".to_owned(),
            "c".to_owned(),
            "d".to_owned(),
            "e".to_owned(),
        ],
        vec!["a".to_owned(), "b".to_owned(), "c".to_owned()],
        vec!["c".to_owned(), "d".to_owned(), "e".to_owned()],
        vec!["b".to_owned(), "c".to_owned()],
    ])
}

#[test]
fn test_tree_generation() {
    let _: SharedFragmentTree = generate_tree();
}

#[test]
fn test_tree_len_builtin() {
    use pyo3::class::sequence::PySequenceProtocol;

    assert_eq!(generate_tree().__len__(), 4)
}

#[test]
fn test_tree_str_builtin() {
    use pyo3::class::basic::PyObjectProtocol;

    let _: String = match generate_tree().__str__() {
        Ok(output) => output,
        Err(_) => panic!("__str__ failed"),
    };
}

#[test]
fn test_tree_size_getter() {
    assert_eq!(generate_tree().size(), 17)
}

#[test]
fn test_asffas_parallel() {
    assert_eq!(
        generate_tree().extract_all_shared_fragments_for_all_strings_parallel(None, None, false),
        vec![
            vec![vec!["c", "d", "e"], vec!["a", "b"]],
            vec![vec!["a", "b", "c"]],
            vec![vec!["c", "d", "e"]],
            vec![vec!["b", "c"]],
        ]
    )
}
