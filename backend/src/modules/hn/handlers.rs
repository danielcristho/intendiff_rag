//! HN module handlers: the verification queue, one candidate, and a decision.

use super::dto::{CandidateQuery, HnSummary, QueueResponse, VerifyRequest};
use super::service;
use crate::app::Shared;
use crate::error::{ApiError, ApiResult, ErrorBody};
use crate::modules::auth::extractor::Annotator;
use crate::shared::clock::now_rfc3339;
use axum::{
    extract::{Query, State},
    Json,
};
use serde_json::Value;

fn text(row: &Value, key: &str) -> String {
    row.get(key)
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string()
}

fn summary(row: &Value) -> HnSummary {
    let list = |key: &str| {
        row.get(key)
            .and_then(Value::as_array)
            .cloned()
            .unwrap_or_default()
    };
    HnSummary {
        id: text(row, "id"),
        name: text(row, "name"),
        before: text(row, "before"),
        after: text(row, "after"),
        source: text(row, "source"),
        queue_position: row
            .get("queue_position")
            .and_then(Value::as_u64)
            .unwrap_or_default(),
        delta: list("delta")
            .iter()
            .filter_map(|v| v.as_str().map(str::to_owned))
            .collect(),
        categories: list("categories")
            .iter()
            .filter_map(|v| v.as_u64().map(|n| n as u8))
            .collect(),
    }
}

#[utoipa::path(get, path = "/api/hn/queue", tag = "hn", security(("session" = [])),
    responses((status = 200, body = QueueResponse), (status = 401, body = ErrorBody)))]
pub async fn get_queue(State(app): State<Shared>, _: Annotator) -> ApiResult<QueueResponse> {
    let candidates = app
        .hn
        .queue()
        .map_err(ApiError::internal)?
        .iter()
        .map(summary)
        .collect();
    let verifications = app.hn.verifications().map_err(ApiError::internal)?;
    Ok(Json(QueueResponse {
        candidates,
        verifications,
    }))
}

#[utoipa::path(get, path = "/api/hn/candidate", tag = "hn", security(("session" = [])), params(CandidateQuery),
    responses((status = 200, body = Object), (status = 400, body = ErrorBody), (status = 401, body = ErrorBody)))]
pub async fn get_candidate(
    State(app): State<Shared>,
    _: Annotator,
    Query(query): Query<CandidateQuery>,
) -> ApiResult<Value> {
    app.hn
        .candidate(&query.id)
        .map_err(ApiError::internal)?
        .map(Json)
        .ok_or(ApiError::BadRequest("unknown candidate id".into()))
}

#[utoipa::path(put, path = "/api/hn/verification", tag = "hn", security(("session" = [])), params(CandidateQuery),
    request_body = VerifyRequest,
    responses((status = 200, body = Object), (status = 400, body = ErrorBody), (status = 401, body = ErrorBody)))]
pub async fn put_verification(
    State(app): State<Shared>,
    Annotator(annotator): Annotator,
    Query(query): Query<CandidateQuery>,
    Json(body): Json<VerifyRequest>,
) -> ApiResult<Value> {
    if app
        .hn
        .candidate(&query.id)
        .map_err(ApiError::internal)?
        .is_none()
    {
        return Err(ApiError::BadRequest("unknown candidate id".into()));
    }
    let entry = service::decide(&body, &annotator, now_rfc3339()).map_err(ApiError::BadRequest)?;
    let _guard = app
        .write_lock
        .lock()
        .map_err(|e| ApiError::internal(e.to_string()))?;
    app.hn
        .save(&query.id, entry.clone())
        .map_err(ApiError::internal)?;
    Ok(Json(Value::Object(entry)))
}
