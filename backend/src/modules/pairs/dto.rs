use serde::{Deserialize, Serialize};
use serde_json::Value;

#[derive(Deserialize)]
pub struct PairQuery {
    pub pair_id: String,
}

#[derive(Serialize)]
pub struct PairsResponse {
    pub source: String,
    pub pairs: Vec<Value>,
}
