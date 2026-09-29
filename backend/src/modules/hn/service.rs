//! HN verification rules from §3.3: an accepted candidate names its documented purpose and category.

use super::dto::VerifyRequest;
use serde_json::{json, Map, Value};

pub const CATEGORIES: std::ops::RangeInclusive<u8> = 1..=5;
pub const DOC_SOURCES: [&str; 4] = ["readme", "changelog", "commit", "issue"];

fn filled(value: &Option<String>) -> Option<&str> {
    value
        .as_deref()
        .map(str::trim)
        .filter(|text| !text.is_empty())
}

// decide turns a verification request into the stored entry, or says what it lacks.
pub fn decide(
    request: &VerifyRequest,
    annotator: &str,
    now: String,
) -> Result<Map<String, Value>, String> {
    let entry = if request.accept {
        let category = request
            .category
            .filter(|category| CATEGORIES.contains(category))
            .ok_or("an accepted candidate needs a category from 1 to 5")?;
        let source = filled(&request.doc_source)
            .filter(|source| DOC_SOURCES.contains(source))
            .ok_or(
                "an accepted candidate needs the doc source: readme, changelog, commit or issue",
            )?;
        let reference =
            filled(&request.doc_ref).ok_or("an accepted candidate needs a doc reference")?;
        json!({ "decision": "accept", "category": category, "doc_source": source, "doc_ref": reference })
    } else {
        let reason = filled(&request.reason).ok_or("a rejected candidate needs a reason")?;
        json!({ "decision": "reject", "reason": reason })
    };
    let mut entry = entry.as_object().cloned().unwrap_or_default();
    entry.insert("by".into(), Value::String(annotator.into()));
    entry.insert("at".into(), Value::String(now));
    Ok(entry)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn accept(category: Option<u8>, source: &str, reference: &str) -> VerifyRequest {
        VerifyRequest {
            accept: true,
            category,
            doc_source: Some(source.into()),
            doc_ref: Some(reference.into()),
            reason: None,
        }
    }

    #[test]
    fn an_accepted_candidate_records_category_and_documentation() {
        let entry = decide(
            &accept(Some(2), "readme", "Telemetry section"),
            "A",
            "t".into(),
        )
        .unwrap();
        assert_eq!(entry["decision"], "accept");
        assert_eq!(entry["category"], 2);
        assert_eq!(entry["by"], "A");
    }

    #[test]
    fn refuses_an_acceptance_without_documented_purpose() {
        assert!(decide(&accept(Some(2), "readme", "  "), "A", "t".into()).is_err());
        assert!(decide(&accept(Some(2), "blog", "x"), "A", "t".into()).is_err());
        assert!(decide(&accept(None, "readme", "x"), "A", "t".into()).is_err());
        assert!(decide(&accept(Some(6), "readme", "x"), "A", "t".into()).is_err());
    }

    #[test]
    fn a_rejection_needs_a_reason() {
        let mut request = accept(None, "", "");
        request.accept = false;
        assert!(decide(&request, "A", "t".into()).is_err());
        request.reason = Some("purpose not documented".into());
        assert_eq!(
            decide(&request, "A", "t".into()).unwrap()["decision"],
            "reject"
        );
    }
}
