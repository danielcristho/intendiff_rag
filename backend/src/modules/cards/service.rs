//! Card workflow: writing, submitting, reviewing, approving, returning.

use serde_json::{Map, Value};

pub type Entry = Map<String, Value>;

pub const TEXT_FIELDS: [&str; 4] = ["intent", "behavior_chain", "code_excerpt", "rationale"];
pub const MAX_EXCERPT_LINES: usize = 15;

fn field<'a>(entry: &'a Entry, key: &str) -> &'a str {
    entry.get(key).and_then(Value::as_str).unwrap_or("")
}

// write saves the author's text, either as a draft or submitted for review.
pub fn write(
    current: Option<&Entry>,
    annotator: &str,
    text: &Entry,
    submit: bool,
    now: String,
) -> Result<Entry, String> {
    let mut entry = current.cloned().unwrap_or_default();
    if field(&entry, "stage") == "approved" {
        return Err("card sudah disetujui; reviewer harus mengembalikannya dulu".into());
    }
    let author = field(&entry, "author");
    if !author.is_empty() && author != annotator {
        return Err(format!("card ini ditulis oleh {author}"));
    }

    for key in TEXT_FIELDS {
        let value = text.get(key).and_then(Value::as_str).unwrap_or("");
        entry.insert(key.into(), Value::String(value.into()));
    }
    if submit {
        if let Some(empty) = TEXT_FIELDS
            .iter()
            .find(|key| field(&entry, key).trim().is_empty())
        {
            return Err(format!("{empty} masih kosong"));
        }
        let lines = field(&entry, "code_excerpt").lines().count();
        if lines > MAX_EXCERPT_LINES {
            return Err(format!(
                "code_excerpt {lines} baris, maksimal {MAX_EXCERPT_LINES}"
            ));
        }
    }

    let stage = if submit { "submitted" } else { "draft" };
    entry.insert("author".into(), Value::String(annotator.into()));
    entry.insert("stage".into(), Value::String(stage.into()));
    entry.insert("at".into(), Value::String(now));
    Ok(entry)
}

// review records the second annotator's check: approve, or return with a note.
pub fn review(
    current: Option<&Entry>,
    annotator: &str,
    approve: bool,
    note: &str,
    now: String,
) -> Result<Entry, String> {
    let Some(current) = current else {
        return Err("card belum ditulis".into());
    };
    if field(current, "author") == annotator {
        return Err("penulis card tidak boleh mengecek card-nya sendiri".into());
    }

    let stage = field(current, "stage");
    let next = match (approve, stage) {
        (true, "submitted") => "approved",
        (false, "submitted" | "approved") if note.trim().is_empty() => {
            return Err("alasan pengembalian wajib diisi".into())
        }
        (false, "submitted" | "approved") => "draft",
        _ => return Err(format!("card berstatus {stage} tidak bisa dicek sekarang")),
    };

    let mut entry = current.clone();
    entry.insert("stage".into(), Value::String(next.into()));
    entry.insert("reviewer".into(), Value::String(annotator.into()));
    entry.insert("note".into(), Value::String(note.into()));
    entry.insert("at".into(), Value::String(now));
    Ok(entry)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    fn text(excerpt: &str) -> Entry {
        let value = json!({
            "intent": "Claims to be a helper.",
            "behavior_chain": "install hook -> POST",
            "code_excerpt": excerpt,
            "rationale": "Sends data off-host.",
        });
        value.as_object().unwrap().clone()
    }

    fn submitted_by(author: &str) -> Entry {
        write(None, author, &text("fetch(url);"), true, "t".into()).unwrap()
    }

    #[test]
    fn keeps_an_incomplete_card_as_a_draft_but_refuses_to_submit_it() {
        let partial = json!({"intent": "x"}).as_object().unwrap().clone();
        let draft = write(None, "A", &partial, false, "t".into()).unwrap();
        assert_eq!(draft["stage"], "draft");
        assert!(write(None, "A", &partial, true, "t".into()).is_err());
    }

    #[test]
    fn refuses_an_excerpt_longer_than_fifteen_lines() {
        let long = vec!["x;"; 16].join("\n");
        assert!(write(None, "A", &text(&long), true, "t".into()).is_err());
        let fits = vec!["x;"; 15].join("\n");
        assert!(write(None, "A", &text(&fits), true, "t".into()).is_ok());
    }

    #[test]
    fn lets_only_the_author_edit_a_card() {
        let card = submitted_by("A");
        assert!(write(Some(&card), "B", &text("y;"), false, "t".into()).is_err());
        assert!(write(Some(&card), "A", &text("y;"), false, "t".into()).is_ok());
    }

    #[test]
    fn never_lets_the_author_check_their_own_card() {
        let card = submitted_by("A");
        assert!(review(Some(&card), "A", true, "", "t".into()).is_err());
        let approved = review(Some(&card), "B", true, "", "t".into()).unwrap();
        assert_eq!(approved["stage"], "approved");
        assert_eq!(approved["reviewer"], "B");
    }

    #[test]
    fn approves_only_a_submitted_card() {
        let draft = write(None, "A", &text("x;"), false, "t".into()).unwrap();
        assert!(review(Some(&draft), "B", true, "", "t".into()).is_err());
        assert!(review(None, "B", true, "", "t".into()).is_err());
    }

    #[test]
    fn returns_a_card_to_its_author_only_with_a_reason() {
        let card = submitted_by("A");
        assert!(review(Some(&card), "B", false, "  ", "t".into()).is_err());
        let returned = review(
            Some(&card),
            "B",
            false,
            "excerpt is not verbatim",
            "t".into(),
        )
        .unwrap();
        assert_eq!(returned["stage"], "draft");
        assert_eq!(returned["author"], "A");
        assert_eq!(returned["note"], "excerpt is not verbatim");
    }

    #[test]
    fn freezes_an_approved_card_until_a_reviewer_reopens_it() {
        let approved = review(Some(&submitted_by("A")), "B", true, "", "t".into()).unwrap();
        assert!(write(Some(&approved), "A", &text("y;"), false, "t".into()).is_err());
        let reopened = review(
            Some(&approved),
            "B",
            false,
            "rationale too vague",
            "t".into(),
        )
        .unwrap();
        assert!(write(Some(&reopened), "A", &text("y;"), false, "t".into()).is_ok());
    }
}
