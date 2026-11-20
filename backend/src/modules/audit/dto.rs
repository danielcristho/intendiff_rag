use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
pub struct AnnotatorQuery {
    pub annotator: String,
}

#[derive(Deserialize)]
pub struct DecisionQuery {
    pub id: String,
    pub annotator: String,
}

#[derive(Serialize)]
pub struct AnnotatorProgress {
    pub annotator: String,
    pub count: usize,
}
