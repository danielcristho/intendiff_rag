//! Data Transfer Objects for the pairs module

use serde::{Deserialize, Serialize};
use serde_json::Value;
use utoipa::{IntoParams, ToSchema};

#[derive(Deserialize, IntoParams)]
pub struct PairQuery {
    pub pair_id: String,
}

#[derive(Serialize, ToSchema)]
pub struct PairsResponse {
    pub source: String,
    #[schema(value_type = Vec<Object>)]
    pub pairs: Vec<Value>,
}
