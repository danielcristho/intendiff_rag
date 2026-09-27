//! Card repository: reading and writing card data and skeletons.

use crate::shared::files::{read_jsonl, read_object, write_atomic};
use serde_json::{Map, Value};
use std::io;
use std::path::{Path, PathBuf};

// Consts
const SKELETON: &str = "kb.skeleton.jsonl";
const CARDS: &str = "kb.cards.json";

pub struct CardRepository {
    dir: PathBuf,
}

impl CardRepository {
    pub fn new(dir: &Path) -> Self {
        Self {
            dir: dir.to_path_buf(),
        }
    }

    pub fn skeleton(&self) -> io::Result<Vec<Value>> {
        read_jsonl(&self.dir.join(SKELETON))
    }

    // exists guards writes: an id missing from the skeleton cannot reach kb.jsonl.
    pub fn exists(&self, id: &str) -> io::Result<bool> {
        Ok(self
            .skeleton()?
            .iter()
            .any(|row| row.get("id").and_then(Value::as_str) == Some(id)))
    }

    pub fn entries(&self) -> io::Result<Map<String, Value>> {
        read_object(&self.dir.join(CARDS))
    }

    pub fn save(&self, id: &str, entry: Map<String, Value>) -> io::Result<()> {
        let mut all = self.entries()?;
        all.insert(id.to_string(), Value::Object(entry));
        write_atomic(&self.dir.join(CARDS), &Value::Object(all))
    }

    pub fn sample_root(&self, id: &str) -> io::Result<Option<PathBuf>> {
        let skeleton = self.skeleton()?;
        let Some(root) = skeleton
            .iter()
            .find(|row| row.get("id").and_then(Value::as_str) == Some(id))
            .and_then(|row| row.get("root").and_then(Value::as_str))
        else {
            return Ok(None);
        };
        let path = self.dir.join(root).canonicalize()?;
        if !path.starts_with(self.dir.canonicalize()?) {
            return Err(io::Error::new(
                io::ErrorKind::InvalidInput,
                "root escapes data dir",
            ));
        }
        Ok(Some(path))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::shared::files::temp_dir;
    use serde_json::json;
    use std::fs;

    #[test]
    fn keeps_other_cards_when_saving_one() {
        let store = CardRepository::new(&temp_dir("cards"));
        let entry = |stage: &str| json!({ "stage": stage }).as_object().unwrap().clone();
        store.save("c1", entry("draft")).unwrap();
        store.save("c2", entry("submitted")).unwrap();
        store.save("c1", entry("submitted")).unwrap();
        let all = store.entries().unwrap();
        assert_eq!(all.len(), 2);
        assert_eq!(all["c1"]["stage"], "submitted");
    }

    #[test]
    fn refuses_a_card_root_outside_the_data_dir() {
        let dir = temp_dir("cards");
        fs::create_dir_all(dir.join("datadog/x")).unwrap();
        fs::write(
            dir.join(SKELETON),
            "{\"id\":\"in\",\"root\":\"datadog/x\"}\n{\"id\":\"out\",\"root\":\"..\"}\n",
        )
        .unwrap();
        let store = CardRepository::new(&dir);
        assert!(store
            .sample_root("in")
            .unwrap()
            .unwrap()
            .ends_with("datadog/x"));
        assert!(store.sample_root("out").is_err());
        assert!(store.sample_root("missing").unwrap().is_none());
        assert!(store.exists("in").unwrap() && !store.exists("missing").unwrap());
    }
}
