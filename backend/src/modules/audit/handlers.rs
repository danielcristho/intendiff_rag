use super::dto::{AnnotatorProgress, AnnotatorQuery, DecisionQuery};
use crate::app::Shared;
use crate::error::{ApiError, ApiResult};
use crate::shared::{clock::now_rfc3339, files::valid_annotator};
use axum::{
    extract::{Query, State},
    Json,
};
use serde_json::Value;

// checked_annotator rejects names that would escape the data directory once used as a filename.
fn checked_annotator(raw: &str) -> Result<&str, ApiError> {
    if valid_annotator(raw) {
        return Ok(raw);
    }
    Err(ApiError::BadRequest(
        "invalid annotator: letters, digits, _ or -, at most 32 characters".into(),
    ))
}

pub async fn get_decisions(
    State(app): State<Shared>,
    Query(query): Query<AnnotatorQuery>,
) -> ApiResult<Value> {
    let annotator = checked_annotator(&query.annotator)?;
    let decisions = app
        .decisions
        .decisions(annotator)
        .map_err(ApiError::internal)?;
    Ok(Json(Value::Object(decisions)))
}

pub async fn put_decision(
    State(app): State<Shared>,
    Query(query): Query<DecisionQuery>,
    Json(patch): Json<Value>,
) -> ApiResult<Value> {
    if query.id.trim().is_empty() {
        return Err(ApiError::BadRequest("id is required".into()));
    }
    let annotator = checked_annotator(&query.annotator)?;
    let _guard = app
        .write_lock
        .lock()
        .map_err(|e| ApiError::internal(e.to_string()))?;
    let merged = app
        .decisions
        .merge(annotator, &query.id, &patch, now_rfc3339())
        .map_err(ApiError::internal)?;
    Ok(Json(merged))
}

// get_annotators reports counts without labels, so no one sees another's verdicts.
pub async fn get_annotators(State(app): State<Shared>) -> ApiResult<Vec<AnnotatorProgress>> {
    let rows = app
        .decisions
        .annotators()
        .map_err(ApiError::internal)?
        .into_iter()
        .map(|(annotator, count)| AnnotatorProgress { annotator, count })
        .collect();
    Ok(Json(rows))
}
