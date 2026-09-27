//! Data Transfer Objects for the cards module.

use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use utoipa::{IntoParams, ToSchema};

#[derive(Deserialize, IntoParams)]
pub struct CardQuery {
    pub id: String,
}

#[derive(Deserialize, IntoParams)]
pub struct FileQuery {
    pub id: String,
    pub path: String,
}

#[derive(Deserialize, ToSchema)]
pub struct WriteCardRequest {
    #[serde(default)]
    pub intent: String,
    #[serde(default)]
    pub behavior_chain: String,
    #[serde(default)]
    pub code_excerpt: String,
    #[serde(default)]
    pub rationale: String,
    #[serde(default)]
    pub submit: bool,
}

impl WriteCardRequest {
    // text returns the four fields in the shape the card workflow stores.
    pub fn text(&self) -> Map<String, Value> {
        [
            ("intent", &self.intent),
            ("behavior_chain", &self.behavior_chain),
            ("code_excerpt", &self.code_excerpt),
            ("rationale", &self.rationale),
        ]
        .into_iter()
        .map(|(key, value)| (key.to_string(), Value::String(value.clone())))
        .collect()
    }
}

#[derive(Deserialize, ToSchema)]
pub struct ReviewCardRequest {
    pub approve: bool,
    #[serde(default)]
    pub note: String,
}

#[derive(Serialize, ToSchema)]
pub struct CardsResponse {
    #[schema(value_type = Vec<Object>)]
    pub cards: Vec<Value>,
    #[schema(value_type = Object)]
    pub entries: Map<String, Value>,
}

#[derive(Serialize, ToSchema)]
pub struct SampleFile {
    pub path: String,
    pub size: u64,
}

#[derive(Serialize, ToSchema)]
pub struct SampleText {
    pub path: String,
    pub text: String,
    pub truncated: bool,
}
