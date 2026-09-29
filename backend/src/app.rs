//! Application state shared by every request handler.

use crate::config::Config;
use crate::modules::{
    audit::repository::DecisionRepository,
    auth::{accounts::Accounts, cookie::SessionCookie, repository::UserRepository, tokens::Tokens},
    cards::repository::CardRepository,
    hn::repository::HnRepository,
    pairs::repository::PairRepository,
};
use std::sync::{Arc, Mutex};

pub struct App {
    pub pairs: PairRepository,
    pub decisions: DecisionRepository,
    pub cards: CardRepository,
    pub hn: HnRepository,
    pub accounts: Accounts,
    pub tokens: Tokens,
    pub cookies: SessionCookie,
    // write_lock serialises read-modify-write on the shared JSON files.
    pub write_lock: Mutex<()>,
}

pub type Shared = Arc<App>;

impl App {
    pub fn new(config: &Config) -> Result<Shared, String> {
        let dir = &config.data_dir;
        Ok(Arc::new(Self {
            pairs: PairRepository::new(dir),
            decisions: DecisionRepository::new(dir),
            cards: CardRepository::new(dir),
            hn: HnRepository::new(dir),
            accounts: Accounts::new(UserRepository::new(dir)),
            tokens: Tokens::new(&config.jwt_secret, config.session.ttl)?,
            cookies: SessionCookie::new(&config.session),
            write_lock: Mutex::new(()),
        }))
    }
}
