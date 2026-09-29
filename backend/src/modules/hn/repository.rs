//! HN repository: the queue hn_queue.py writes and the verification decisions.

use crate::shared::files::{read_jsonl, read_object, write_atomic};
use serde_json::{Map, Value};
use std::io;
use std::path::{Path, PathBuf};

// Consts
const QUEUE: &str = "hn/queue.jsonl";
const VERIFICATIONS: &str = "hn_verification.json";

pub struct HnRepository {
    dir: PathBuf,
}

impl HnRepository {
    pub fn new(dir: &Path) -> Self {
        Self {
            dir: dir.to_path_buf(),
        }
    }

    pub fn queue(&self) -> io::Result<Vec<Value>> {
        read_jsonl(&self.dir.join(QUEUE))
    }

    pub fn candidate(&self, id: &str) -> io::Result<Option<Value>> {
        Ok(self
            .queue()?
            .into_iter()
            .find(|row| row.get("id").and_then(Value::as_str) == Some(id)))
    }

    pub fn verifications(&self) -> io::Result<Map<String, Value>> {
        read_object(&self.dir.join(VERIFICATIONS))
    }

    pub fn save(&self, id: &str, entry: Map<String, Value>) -> io::Result<()> {
        let mut all = self.verifications()?;
        all.insert(id.to_string(), Value::Object(entry));
        write_atomic(&self.dir.join(VERIFICATIONS), &Value::Object(all))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::shared::files::temp_dir;
    use serde_json::json;

    #[test]
    fn finds_a_queued_candidate_and_keeps_other_decisions() {
        let dir = temp_dir("hn");
        std::fs::create_dir_all(dir.join("hn")).unwrap();
        std::fs::write(dir.join(QUEUE), "{\"id\":\"a@1\"}\n{\"id\":\"b@2\"}\n").unwrap();
        let store = HnRepository::new(&dir);
        assert!(store.candidate("b@2").unwrap().is_some());
        assert!(store.candidate("c@3").unwrap().is_none());
        let entry = |d: &str| json!({ "decision": d }).as_object().unwrap().clone();
        store.save("a@1", entry("accept")).unwrap();
        store.save("b@2", entry("reject")).unwrap();
        assert_eq!(store.verifications().unwrap().len(), 2);
    }
}
