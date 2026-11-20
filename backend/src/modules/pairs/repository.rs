// pairs.jsonl and results.jsonl are written by the Python pipeline; this side only reads.

use crate::shared::files::{existing_or_sample, read_jsonl};
use serde_json::Value;
use std::io;
use std::path::{Path, PathBuf};

pub struct PairRepository {
    dir: PathBuf,
}

impl PairRepository {
    pub fn new(dir: &Path) -> Self {
        Self {
            dir: dir.to_path_buf(),
        }
    }

    pub fn pairs(&self) -> io::Result<(String, Vec<Value>)> {
        let path = existing_or_sample(&self.dir, "pairs.jsonl", "pairs.sample.jsonl");
        let source = path
            .file_name()
            .map(|name| name.to_string_lossy().into_owned())
            .unwrap_or_default();
        Ok((source, read_jsonl(&path)?))
    }

    pub fn results(&self, pair_id: &str) -> io::Result<Vec<Value>> {
        let path = existing_or_sample(&self.dir, "results.jsonl", "results.sample.jsonl");
        Ok(read_jsonl(&path)?
            .into_iter()
            .filter(|row| row.get("pair_id").and_then(Value::as_str) == Some(pair_id))
            .collect())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::shared::files::temp_dir;
    use std::fs;

    #[test]
    fn falls_back_to_the_sample_until_the_real_dataset_exists() {
        let dir = temp_dir("pairs");
        let store = PairRepository::new(&dir);
        fs::write(dir.join("pairs.sample.jsonl"), "{\"id\":\"a\"}\n").unwrap();
        assert_eq!(store.pairs().unwrap().0, "pairs.sample.jsonl");
        fs::write(dir.join("pairs.jsonl"), "{\"id\":\"b\"}\n").unwrap();
        assert_eq!(store.pairs().unwrap().0, "pairs.jsonl");
    }

    #[test]
    fn returns_only_the_runs_belonging_to_one_pair() {
        let dir = temp_dir("pairs");
        fs::write(
            dir.join("results.jsonl"),
            "{\"pair_id\":\"a\",\"config\":\"DIFF+I\"}\n{\"pair_id\":\"b\",\"config\":\"DIFF+I\"}\n{\"pair_id\":\"a\",\"config\":\"DIFF+I+MB\"}\n",
        )
        .unwrap();
        let store = PairRepository::new(&dir);
        let rows = store.results("a").unwrap();
        assert_eq!(rows.len(), 2);
        assert!(rows.iter().all(|row| row["pair_id"] == "a"));
        assert!(store.results("missing").unwrap().is_empty());
    }
}
