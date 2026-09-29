//! Data Transfer Objects for the HN module.

use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use utoipa::{IntoParams, ToSchema};

#[derive(Deserialize, IntoParams)]
pub struct CandidateQuery {
    pub id: String,
}

// HnSummary is one queue row without its diff, which the detail endpoint serves.
#[derive(Serialize, ToSchema)]
pub struct HnSummary {
    pub id: String,
    pub name: String,
    pub before: String,
    pub after: String,
    pub source: String,
    pub queue_position: u64,
    pub delta: Vec<String>,
    // categories lists the §3.3 categories the delta's signals could satisfy.
    pub categories: Vec<u8>,
}

#[derive(Serialize, ToSchema)]
pub struct QueueResponse {
    pub candidates: Vec<HnSummary>,
    #[schema(value_type = Object)]
    pub verifications: Map<String, Value>,
}

#[derive(Deserialize, ToSchema)]
pub struct VerifyRequest {
    pub accept: bool,
    pub category: Option<u8>,
    // doc_source is where the purpose is documented: readme, changelog, commit or issue.
    pub doc_source: Option<String>,
    pub doc_ref: Option<String>,
    pub reason: Option<String>,
}
