//! Repository for storing and retrieving audit decisions in JSON files.

use crate::shared::files::{read_object, valid_annotator, write_atomic};
use serde_json::{Map, Value};
use std::path::{Path, PathBuf};
use std::{fs, io};

const PREFIX: &str = "audit_decisions.";
const SUFFIX: &str = ".json";

pub struct DecisionRepository {
    dir: PathBuf,
}

impl DecisionRepository {
    pub fn new(dir: &Path) -> Self {
        Self {
            dir: dir.to_path_buf(),
        }
    }

    fn path(&self, annotator: &str) -> PathBuf {
        self.dir.join(format!("{PREFIX}{annotator}{SUFFIX}"))
    }

    pub fn decisions(&self, annotator: &str) -> io::Result<Map<String, Value>> {
        read_object(&self.path(annotator))
    }

    // annotators lists each annotator and how many decisions they have recorded.
    pub fn annotators(&self) -> io::Result<Vec<(String, usize)>> {
        let mut found = Vec::new();
        if !self.dir.exists() {
            return Ok(found);
        }
        for entry in fs::read_dir(&self.dir)? {
            let filename = entry?.file_name().to_string_lossy().into_owned();
            let Some(name) = filename
                .strip_prefix(PREFIX)
                .and_then(|rest| rest.strip_suffix(SUFFIX))
            else {
                continue;
            };
            if valid_annotator(name) {
                found.push((name.to_string(), self.decisions(name)?.len()));
            }
        }
        found.sort();
        Ok(found)
    }

    // merge applies a patch to one decision instead of replacing it.
    pub fn merge(
        &self,
        annotator: &str,
        id: &str,
        patch: &Value,
        now: String,
    ) -> io::Result<Value> {
        let mut all = self.decisions(annotator)?;
        let mut entry = match all.get(id) {
            Some(Value::Object(existing)) => existing.clone(),
            _ => Map::new(),
        };
        if let Value::Object(fields) = patch {
            for (key, value) in fields {
                entry.insert(key.clone(), value.clone());
            }
        }
        entry.insert("at".into(), Value::String(now));

        let merged = Value::Object(entry);
        all.insert(id.to_string(), merged.clone());
        write_atomic(&self.path(annotator), &Value::Object(all))?;
        Ok(merged)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::shared::files::temp_dir;
    use serde_json::json;

    fn store() -> DecisionRepository {
        DecisionRepository::new(&temp_dir("decisions"))
    }

    #[test]
    fn treats_a_missing_file_as_no_decisions() {
        assert!(store().decisions("A").unwrap().is_empty());
    }

    #[test]
    fn merges_a_patch_instead_of_replacing_the_decision() {
        let store = store();
        store
            .merge("A", "p1", &json!({"label": "benign"}), "t1".into())
            .unwrap();
        let out = store
            .merge("A", "p1", &json!({"note": "unsure"}), "t2".into())
            .unwrap();
        assert_eq!(out["label"], "benign");
        assert_eq!(out["note"], "unsure");
        assert_eq!(out["at"], "t2");
    }

    #[test]
    fn keeps_decisions_on_other_pairs_when_writing_one() {
        let store = store();
        store
            .merge("A", "p1", &json!({"label": "benign"}), "t1".into())
            .unwrap();
        store
            .merge("A", "p2", &json!({"label": "malicious"}), "t2".into())
            .unwrap();
        let all = store.decisions("A").unwrap();
        assert_eq!(all.len(), 2);
        assert_eq!(all["p1"]["label"], "benign");
    }

    #[test]
    fn keeps_two_annotators_verdicts_on_the_same_pair_apart() {
        let store = store();
        store
            .merge("A", "p1", &json!({"label": "benign"}), "t1".into())
            .unwrap();
        store
            .merge("B", "p1", &json!({"label": "malicious"}), "t2".into())
            .unwrap();
        assert_eq!(store.decisions("A").unwrap()["p1"]["label"], "benign");
        assert_eq!(store.decisions("B").unwrap()["p1"]["label"], "malicious");
    }

    #[test]
    fn counts_annotators_without_exposing_their_labels() {
        let store = store();
        store
            .merge("A", "p1", &json!({"label": "benign"}), "t".into())
            .unwrap();
        store
            .merge("A", "p2", &json!({"label": "benign"}), "t".into())
            .unwrap();
        store
            .merge("B", "p1", &json!({"label": "malicious"}), "t".into())
            .unwrap();
        fs::write(store.dir.join("audit_decisions.json"), "{}").unwrap();
        assert_eq!(
            store.annotators().unwrap(),
            vec![("A".into(), 2), ("B".into(), 1)]
        );
    }
}
