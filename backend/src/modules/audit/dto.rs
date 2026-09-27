// Data Transfer Objects for the audit module

use serde::{Deserialize, Serialize};
use utoipa::{IntoParams, ToSchema};

#[derive(Deserialize, IntoParams)]
pub struct DecisionQuery {
    pub id: String,
}

#[derive(Serialize, ToSchema)]
pub struct AnnotatorProgress {
    pub annotator: String,
    pub count: usize,
}
