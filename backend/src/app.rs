use crate::modules::{audit::repository::DecisionRepository, pairs::repository::PairRepository};
use std::path::Path;
use std::sync::{Arc, Mutex};

pub struct App {
    pub pairs: PairRepository,
    pub decisions: DecisionRepository,
    // write_lock serialises read-modify-write on the decision files.
    pub write_lock: Mutex<()>,
}

pub type Shared = Arc<App>;

impl App {
    pub fn new(data_dir: &Path) -> Shared {
        Arc::new(Self {
            pairs: PairRepository::new(data_dir),
            decisions: DecisionRepository::new(data_dir),
            write_lock: Mutex::new(()),
        })
    }
}
