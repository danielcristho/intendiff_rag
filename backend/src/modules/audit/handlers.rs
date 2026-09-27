use super::dto::{AnnotatorProgress, DecisionQuery};
use crate::app::Shared;
use crate::error::{ApiError, ApiResult, ErrorBody};
use crate::modules::auth::extractor::Annotator;
use crate::shared::clock::now_rfc3339;
use axum::{
    extract::{Query, State},
    Json,
};
use serde_json::Value;

// get_decisions returns all decisions for the given annotator, including labels and verdicts.
#[utoipa::path(get, path = "/api/decisions", tag = "audit", security(("session" = [])),
    responses((status = 200, body = Object), (status = 401, body = ErrorBody)))]
pub async fn get_decisions(
    State(app): State<Shared>,
    Annotator(annotator): Annotator,
) -> ApiResult<Value> {
    let decisions = app
        .decisions
        .decisions(&annotator)
        .map_err(ApiError::internal)?;
    Ok(Json(Value::Object(decisions)))
}

// put_decision merges the given patch into the existing decision for the given annotator and id.
#[utoipa::path(put, path = "/api/decisions", tag = "audit", security(("session" = [])), params(DecisionQuery), request_body = Object,
    responses((status = 200, body = Object), (status = 400, body = ErrorBody), (status = 401, body = ErrorBody)))]
pub async fn put_decision(
    State(app): State<Shared>,
    Annotator(annotator): Annotator,
    Query(query): Query<DecisionQuery>,
    Json(patch): Json<Value>,
) -> ApiResult<Value> {
    if query.id.trim().is_empty() {
        return Err(ApiError::BadRequest("id is required".into()));
    }
    let _guard = app
        .write_lock
        .lock()
        .map_err(|e| ApiError::internal(e.to_string()))?;
    let merged = app
        .decisions
        .merge(&annotator, &query.id, &patch, now_rfc3339())
        .map_err(ApiError::internal)?;
    Ok(Json(merged))
}

// get_annotators reports counts without labels, so no one sees another's verdicts.
#[utoipa::path(get, path = "/api/annotators", tag = "audit", security(("session" = [])),
    responses((status = 200, body = Vec<AnnotatorProgress>), (status = 401, body = ErrorBody)))]
pub async fn get_annotators(
    State(app): State<Shared>,
    _: Annotator,
) -> ApiResult<Vec<AnnotatorProgress>> {
    let rows = app
        .decisions
        .annotators()
        .map_err(ApiError::internal)?
        .into_iter()
        .map(|(annotator, count)| AnnotatorProgress { annotator, count })
        .collect();
    Ok(Json(rows))
}
