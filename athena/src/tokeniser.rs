use html2text::from_read_raw as html2text;
use itertools::Itertools;
use lazy_static::lazy_static;
use regex::{escape, Regex};

const URL_PATTERN: &str =
    r#"(?:http|ftp)[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"#;

lazy_static! {
    static ref TOKEN_RE: Regex = Regex::new(
        r"(?x)
        (?:[^\w]*)                    # Capture non-word characters before the token
        (?P<token>(?:\w+[-'.+:])*\w+) # Capture the token
        (?:[^\w]*)                    # Capture non-word characters after the token
    "
    )
    .unwrap();
}

fn extract_text_from_json(json: serde_json::Value, acc: &mut String) {
    use serde_json::Value::*;

    match json {
        Null => acc.push_str("None "),
        Bool(b) => acc.push_str(if b { "True " } else { "False " }),
        Number(n) => acc.push_str(&format!("{} ", n)),
        String(s) => {
            acc.push_str(&s);
            acc.push(' ');
        }
        Array(vals) => vals
            .into_iter()
            .for_each(|v| extract_text_from_json(v, acc)),
        Object(dict) => dict
            .into_iter()
            .for_each(|(_k, v)| extract_text_from_json(v, acc)),
    }
}

pub fn tokenise_and_join_with_spaces(content: &[u8], exclusions: &[&str]) -> String {
    let parsed_html_text = html2text(content);

    // Allocate a String with sufficient capacity for the text without JSON
    let mut parsed_html_text_no_json = String::with_capacity(parsed_html_text.len());

    // json_search_pos is the byte index from which we will search for JSON
    let mut json_search_pos: usize = 0;

    // Replace inline JSON with its textual content
    while let Some(json_match) = parsed_html_text[json_search_pos..].find(|c| c == '{' || c == '[')
    {
        parsed_html_text_no_json
            .push_str(&parsed_html_text[json_search_pos..(json_search_pos + json_match)]);

        json_search_pos += json_match;

        let mut deserialiser =
            serde_json::Deserializer::from_str(&parsed_html_text[json_search_pos..])
                .into_iter::<serde_json::Value>();

        if let Some(Ok(json)) = deserialiser.next() {
            // Valid JSON was found and can be extracted
            extract_text_from_json(json, &mut parsed_html_text_no_json);

            json_search_pos += deserialiser.byte_offset();
        } else if let Some((next_char_byte_offset, _c)) =
            parsed_html_text[json_search_pos..].char_indices().nth(1)
        {
            // No valid JSON was found but we can advance to the next character
            parsed_html_text_no_json.push_str(
                &parsed_html_text[json_search_pos..(json_search_pos + next_char_byte_offset)],
            );

            json_search_pos += next_char_byte_offset;
        } else {
            // No valid JSON was found and the end of the document has been reached
            break;
        }
    }

    // Push the remaining non-JSON content into the processed string buffer
    parsed_html_text_no_json.push_str(&parsed_html_text[json_search_pos..]);

    // Create the Regex pattern to capture all URLs and exclusions in the text
    // Only checks for ASCII word boundaries around an exclusion to use the DFA
    // (see https://github.com/rust-lang/regex/blob/master/PERFORMANCE.md#
    //      unicode-word-boundaries-may-prevent-the-dfa-from-being-used)
    let pattern = std::iter::once(URL_PATTERN.to_owned())
        .chain(exclusions.iter().copied().map(escape))
        .map(|p| format!(r"(?:(?-u:\b){}(?-u:\b))", p))
        .join("|");

    // Remove all URLs and exclusions from the text
    let parsed_html_text_no_json_or_links_or_exclusions = Regex::new(&pattern)
        .unwrap()
        .replace_all(&parsed_html_text_no_json, "");

    // Extract only the tokens, remove all extraneous whitespaces
    // Then join the tokens with spaces and put them into lower case
    TOKEN_RE
        .replace_all(&parsed_html_text_no_json_or_links_or_exclusions, "$token ")
        .trim()
        .to_lowercase()
}
