use super::{tokenise_and_join_with_spaces as tokenise, SharedFragmentTree};

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

    let _: String = generate_tree().__str__().unwrap();
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

#[test]
fn test_tokenise_lowercase() {
    assert_eq!(&tokenise("HeLL0", Vec::new()), "hell0")
}

#[test]
fn test_tokenise_split_space() {
    assert_eq!(
        &tokenise("Hello    World \t \nHow  \n\tare you", Vec::new()),
        "hello world how are you"
    )
}

#[test]
fn test_tokenise_words() {
    assert_eq!(
        &tokenise(
            r"Hello World! Let's go and use cmd-iaso+athena.tokenise?!
            What about snake_case: what a great quest:ion.",
            Vec::new()
        ),
        concat!(
            "hello world let's go and use cmd-iaso+athena.tokenise what about ",
            "snake_case what a great quest:ion"
        )
    )
}

#[test]
fn test_tokenise_no_urls() {
    assert_eq!(
        &tokenise(
            "This is a http http://github.com/identifiers-org/ URL",
            Vec::new()
        ),
        "this is a http url"
    );
    assert_eq!(
        &tokenise(
            "This is a https https://github.com/identifiers-org/cmd-iaso URL",
            Vec::new()
        ),
        "this is a https url"
    );
    assert_eq!(
        &tokenise(
            "This is a ftp ftp://github.com/identifiers-org/cmd-iaso?q=hi&a=%17 URL",
            Vec::new()
        ),
        "this is a ftp url"
    );
    assert_eq!(
        &tokenise(
            "This is a ftps ftps://github.com/identifiers-org/cmd-iaso?q=hi&a=%17#hoho URL",
            Vec::new()
        ),
        "this is a ftps url"
    );
}

#[test]
fn test_tokenise_exclude() {
    assert_eq!(&tokenise("hel.o el.o el.oha", vec!["el.o"]), "hel.o el.oha")
}

#[test]
fn test_tokenise_json() {
    assert_eq!(
        &tokenise(
            r#"[false,{"bycicle":42,"dream":null,"sugar":"castle"},"driven"]"#,
            Vec::new()
        ),
        "false 42 none castle driven"
    )
}

#[test]
fn test_tokenise_xml() {
    assert_eq!(
        &tokenise(
            r#"<?xml version="1.0" encoding="UTF-8" ?><root><came east="opinion">down</came>
            <but frame="breathe">passage</but></root>"#,
            Vec::new()
        ),
        "down passage"
    )
}

#[test]
fn test_tokenise_html() {
    assert_eq!(
        &tokenise(
            r#"<!DOCTYPE html>
<html>
  <head>
    This will be included.
  </head>
  <style>
    html::-webkit-scrollbar {
      display: none;
    }
  </style>
  <script>
    console.log("Hello world!");
  </script>
  <body>
    <h1>My First Heading</h1>
    <p>My first paragraph.</p>
    My first <a href="https://github.com/identifiers-org/cmd-iaso">link</a>
  </body>
</html>
"#,
            Vec::new()
        ),
        "this will be included my first heading my first paragraph my first link"
    )
}

#[test]
fn test_tokenise_mixed() {
    assert_eq!(
        &tokenise(
            r#"<!DOCTYPE html>
<html>
  <body>
    <pre>
      ["html", "xml", "json": {"hi": 42}]
    </pre>
    Who likes some raw text?
</html>
"#,
            vec!["ml", "xml", "raw", "Who"]
        ),
        "html json 42 likes some text"
    )
}
