// Reads update pairs and writes audit decisions, backed by plain files.

use serde_json::{Map, Value};
use std::path::{Path, PathBuf};
use std::{fs, io};

const PREFIX: &str = "audit_decisions.";
const SUFFIX: &str = ".json";

// Store resolves and reads the project's data directory.
pub struct Store {
    pub data_dir: PathBuf,
}

// valid_annotator reports whether a name is safe to use as part of a filename.
pub fn valid_annotator(name: &str) -> bool {
    !name.is_empty()
        && name.len() <= 32
        && name.chars().all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-')
}

// read_jsonl parses one JSON value per non-blank line, or nothing if absent.
pub fn read_jsonl(path: &Path) -> io::Result<Vec<Value>> {
    if !path.exists() {
        return Ok(Vec::new());
    }
    let text = fs::read_to_string(path)?;
    text.lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| serde_json::from_str(line).map_err(io::Error::other))
        .collect()
}

// existing_or_sample prefers the real dataset and falls back to the fixture.
fn existing_or_sample(dir: &Path, name: &str, sample: &str) -> PathBuf {
    let real = dir.join(name);
    if real.exists() {
        real
    } else {
        dir.join(sample)
    }
}

impl Store {
    // new points a store at the directory holding the project's data files.
    pub fn new(data_dir: PathBuf) -> Self {
        Self { data_dir }
    }

    // pairs_path returns the pairs file in use, real dataset or fixture.
    pub fn pairs_path(&self) -> PathBuf {
        existing_or_sample(&self.data_dir, "pairs.jsonl", "pairs.sample.jsonl")
    }

    // decisions_path returns where one annotator's decisions are stored.
    pub fn decisions_path(&self, annotator: &str) -> PathBuf {
        self.data_dir.join(format!("{PREFIX}{annotator}{SUFFIX}"))
    }

    // pairs returns every update pair along with the filename it came from.
    pub fn pairs(&self) -> io::Result<(String, Vec<Value>)> {
        let path = self.pairs_path();
        let source = path
            .file_name()
            .map(|name| name.to_string_lossy().into_owned())
            .unwrap_or_default();
        Ok((source, read_jsonl(&path)?))
    }

    // decisions returns one annotator's decisions, empty if they have none yet.
    pub fn decisions(&self, annotator: &str) -> io::Result<Map<String, Value>> {
        let path = self.decisions_path(annotator);
        if !path.exists() {
            return Ok(Map::new());
        }
        match serde_json::from_str(&fs::read_to_string(&path)?) {
            Ok(Value::Object(map)) => Ok(map),
            _ => Ok(Map::new()),
        }
    }

    // annotators lists each annotator and how many decisions they have recorded.
    pub fn annotators(&self) -> io::Result<Vec<(String, usize)>> {
        let mut found = Vec::new();
        if !self.data_dir.exists() {
            return Ok(found);
        }
        for entry in fs::read_dir(&self.data_dir)? {
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

    // merge_decision applies a patch to one pair's decision and rewrites the file.
    pub fn merge_decision(
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

        fs::create_dir_all(&self.data_dir)?;
        // Write to a temp file and rename.
        let target = self.decisions_path(annotator);
        let tmp = target.with_extension("tmp");
        fs::write(&tmp, serde_json::to_string_pretty(&Value::Object(all))?)?;
        fs::rename(&tmp, &target)?;
        Ok(merged)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    static SEQ: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);

    // temp_store creates an empty store in a directory unique to one test.
    fn temp_store() -> Store {
        let n = SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
        let dir = std::env::temp_dir().join(format!("idr-test-{}-{n}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        Store::new(dir)
    }

    #[test]
    fn skips_blank_lines_when_reading_jsonl() {
        let store = temp_store();
        let path = store.data_dir.join("pairs.jsonl");
        fs::write(&path, "{\"id\":\"a\"}\n\n{\"id\":\"b\"}\n").unwrap();
        assert_eq!(read_jsonl(&path).unwrap().len(), 2);
    }

    #[test]
    fn treats_a_missing_file_as_empty_rather_than_an_error() {
        let store = temp_store();
        assert!(store.decisions("A").unwrap().is_empty());
        assert!(read_jsonl(&store.data_dir.join("missing.jsonl")).unwrap().is_empty());
    }

    #[test]
    fn falls_back_to_the_sample_until_the_real_dataset_exists() {
        let store = temp_store();
        fs::write(store.data_dir.join("pairs.sample.jsonl"), "{\"id\":\"a\"}\n").unwrap();
        assert!(store.pairs_path().ends_with("pairs.sample.jsonl"));
        fs::write(store.data_dir.join("pairs.jsonl"), "{\"id\":\"b\"}\n").unwrap();
        assert!(store.pairs_path().ends_with("pairs.jsonl"));
    }

    #[test]
    fn rejects_annotator_names_that_escape_the_data_dir() {
        for bad in ["", "../etc", "a/b", "a.b", "a b", "..", &"x".repeat(33)] {
            assert!(!valid_annotator(bad), "should reject: {bad:?}");
        }
        for good in ["A", "robby", "daniel-2", "annotator_B"] {
            assert!(valid_annotator(good), "should accept: {good:?}");
        }
    }

    #[test]
    fn merges_a_patch_instead_of_replacing_the_decision() {
        let store = temp_store();
        store.merge_decision("A", "p1", &json!({"label": "benign"}), "t1".into()).unwrap();
        let out = store.merge_decision("A", "p1", &json!({"note": "unsure"}), "t2".into()).unwrap();
        assert_eq!(out["label"], "benign");
        assert_eq!(out["note"], "unsure");
        assert_eq!(out["at"], "t2");
    }

    #[test]
    fn keeps_decisions_on_other_pairs_when_writing_one() {
        let store = temp_store();
        store.merge_decision("A", "p1", &json!({"label": "benign"}), "t1".into()).unwrap();
        store.merge_decision("A", "p2", &json!({"label": "malicious"}), "t2".into()).unwrap();
        let all = store.decisions("A").unwrap();
        assert_eq!(all.len(), 2);
        assert_eq!(all["p1"]["label"], "benign");
    }

    #[test]
    fn keeps_two_annotators_verdicts_on_the_same_pair_apart() {
        let store = temp_store();
        store.merge_decision("A", "p1", &json!({"label": "benign"}), "t1".into()).unwrap();
        store.merge_decision("B", "p1", &json!({"label": "malicious"}), "t2".into()).unwrap();
        assert_eq!(store.decisions("A").unwrap()["p1"]["label"], "benign");
        assert_eq!(store.decisions("B").unwrap()["p1"]["label"], "malicious");
    }

    #[test]
    fn counts_annotators_without_exposing_their_labels() {
        let store = temp_store();
        store.merge_decision("A", "p1", &json!({"label": "benign"}), "t".into()).unwrap();
        store.merge_decision("A", "p2", &json!({"label": "benign"}), "t".into()).unwrap();
        store.merge_decision("B", "p1", &json!({"label": "malicious"}), "t".into()).unwrap();
        fs::write(store.data_dir.join("audit_decisions.json"), "{}").unwrap();
        assert_eq!(store.annotators().unwrap(), vec![("A".into(), 2), ("B".into(), 1)]);
    }
}
