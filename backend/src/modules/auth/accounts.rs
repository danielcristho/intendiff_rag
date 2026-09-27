//! Accounts module for managing user accounts and authentication.

use crate::modules::auth::repository::UserRepository;
use crate::shared::files::valid_annotator;
use argon2::{
    password_hash::{phc::PasswordHash, PasswordHasher, PasswordVerifier},
    Argon2,
};
use std::sync::OnceLock;

pub const MIN_PASSWORD: usize = 8;

#[derive(Clone)]
pub struct Accounts {
    store: UserRepository,
}

// dummy_hash returns a fixed hash for a known password, so that timing attacks cannot reveal whether an account exists.
fn dummy_hash() -> &'static str {
    static HASH: OnceLock<String> = OnceLock::new();
    HASH.get_or_init(|| {
        Argon2::default()
            .hash_password(b"not-a-real-password")
            .expect("argon2 hashes a fixed input")
            .to_string()
    })
}

// matches checks whether the given password matches the stored hash, returning false if the hash is invalid.
fn matches(password: &str, stored: &str) -> bool {
    PasswordHash::new(stored)
        .map(|hash| {
            Argon2::default()
                .verify_password(password.as_bytes(), &hash)
                .is_ok()
        })
        .unwrap_or(false)
}

impl Accounts {
    pub fn new(store: UserRepository) -> Self {
        Self { store }
    }

    // add creates or replaces an account, which makes it the password reset.
    pub fn add(&self, name: &str, password: &str) -> Result<(), String> {
        if !valid_annotator(name) {
            return Err("username: letters, digits, _ or -, at most 32 characters".into());
        }
        if password.chars().count() < MIN_PASSWORD {
            return Err(format!("password needs at least {MIN_PASSWORD} characters"));
        }
        let hash = Argon2::default()
            .hash_password(password.as_bytes())
            .map_err(|err| err.to_string())?
            .to_string();
        self.store
            .set_hash(name, hash)
            .map_err(|err| err.to_string())
    }

    pub fn verify(&self, name: &str, password: &str) -> bool {
        match self.store.hash(name) {
            Some(stored) => matches(password, &stored),
            None => {
                matches(password, dummy_hash());
                false
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::shared::files::temp_dir;

    fn accounts() -> (Accounts, std::path::PathBuf) {
        let dir = temp_dir("accounts");
        (Accounts::new(UserRepository::new(&dir)), dir)
    }

    #[test]
    fn accepts_only_the_password_that_was_set() {
        let (accounts, _) = accounts();
        accounts.add("userme", "correct horse").unwrap();
        assert!(accounts.verify("userme", "correct horse"));
        assert!(!accounts.verify("userme", "wrong horse!"));
        assert!(!accounts.verify("nobody", "correct horse"));
    }

    #[test]
    fn never_writes_the_plaintext_password() {
        let (accounts, dir) = accounts();
        accounts.add("userme", "correct horse").unwrap();
        let stored = std::fs::read_to_string(dir.join("users.json")).unwrap();
        assert!(!stored.contains("correct horse"));
        assert!(stored.contains("$argon2id$"));
    }

    #[test]
    fn replaces_the_password_on_a_second_add() {
        let (accounts, _) = accounts();
        accounts.add("userme", "first password").unwrap();
        accounts.add("userme", "second password").unwrap();
        assert!(!accounts.verify("userme", "first password"));
        assert!(accounts.verify("userme", "second password"));
    }

    #[test]
    fn refuses_unsafe_usernames_and_short_passwords() {
        let (accounts, _) = accounts();
        assert!(accounts.add("../etc", "long enough").is_err());
        assert!(accounts.add("userme", "short").is_err());
    }
}
