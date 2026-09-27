//! Repository for managing user accounts and their password hashes.

use crate::shared::files::{read_object, write_atomic};
use serde_json::Value;
use std::io;
use std::path::{Path, PathBuf};

const USERS: &str = "users.json";

#[derive(Clone)]
pub struct UserRepository {
    path: PathBuf,
}

impl UserRepository {
    pub fn new(dir: &Path) -> Self {
        Self {
            path: dir.join(USERS),
        }
    }

    pub fn hash(&self, name: &str) -> Option<String> {
        read_object(&self.path)
            .ok()?
            .get(name)
            .and_then(Value::as_str)
            .map(str::to_owned)
    }

    pub fn set_hash(&self, name: &str, hash: String) -> io::Result<()> {
        let mut all = read_object(&self.path)?;
        all.insert(name.to_string(), Value::String(hash));
        write_atomic(&self.path, &Value::Object(all))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::shared::files::temp_dir;

    #[test]
    fn keeps_other_accounts_when_setting_one() {
        let store = UserRepository::new(&temp_dir("users"));
        store.set_hash("A", "h1".into()).unwrap();
        store.set_hash("B", "h2".into()).unwrap();
        store.set_hash("A", "h3".into()).unwrap();
        assert_eq!(store.hash("A").as_deref(), Some("h3"));
        assert_eq!(store.hash("B").as_deref(), Some("h2"));
        assert!(store.hash("C").is_none());
    }
}
