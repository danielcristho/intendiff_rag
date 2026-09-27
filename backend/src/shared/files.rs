// File helpers every repository uses; data/ is shared with the Python pipeline.

use serde_json::{Map, Value};
use std::path::{Path, PathBuf};
use std::{fs, io};

// valid_annotator reports whether a name is safe to use as part of a filename.
pub fn valid_annotator(name: &str) -> bool {
    !name.is_empty()
        && name.len() <= 32
        && name
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || c == '_' || c == '-')
}

// read_jsonl reads a JSONL file, returning an empty vector if the file is missing.
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

// read_object reads a JSON object from a file, returning an empty map if the file is missing or invalid.
pub fn read_object(path: &Path) -> io::Result<Map<String, Value>> {
    if !path.exists() {
        return Ok(Map::new());
    }
    match serde_json::from_str(&fs::read_to_string(path)?) {
        Ok(Value::Object(map)) => Ok(map),
        _ => Ok(Map::new()),
    }
}

// write_atomic writes a file in a way that avoids leaving a half-written file if the process is interrupted.
pub fn write_atomic(target: &Path, value: &Value) -> io::Result<()> {
    if let Some(dir) = target.parent() {
        fs::create_dir_all(dir)?;
    }
    let tmp = target.with_extension("tmp");
    fs::write(&tmp, serde_json::to_string_pretty(value)?)?;
    fs::rename(&tmp, target)
}

pub fn existing_or_sample(dir: &Path, name: &str, sample: &str) -> PathBuf {
    let real = dir.join(name);
    if real.exists() {
        real
    } else {
        dir.join(sample)
    }
}

#[cfg(test)]
pub(crate) fn temp_dir(tag: &str) -> PathBuf {
    static SEQ: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
    let n = SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let dir = std::env::temp_dir().join(format!("idr-{tag}-{}-{n}", std::process::id()));
    let _ = fs::remove_dir_all(&dir);
    fs::create_dir_all(&dir).unwrap();
    dir
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn skips_blank_lines_when_reading_jsonl() {
        let path = temp_dir("files").join("pairs.jsonl");
        fs::write(&path, "{\"id\":\"a\"}\n\n{\"id\":\"b\"}\n").unwrap();
        assert_eq!(read_jsonl(&path).unwrap().len(), 2);
    }

    #[test]
    fn treats_a_missing_file_as_empty_rather_than_an_error() {
        let dir = temp_dir("files");
        assert!(read_jsonl(&dir.join("missing.jsonl")).unwrap().is_empty());
        assert!(read_object(&dir.join("missing.json")).unwrap().is_empty());
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
}
