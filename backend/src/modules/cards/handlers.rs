//! Card module handlers: HTTP endpoints for knowledge-base cards, their skeletons, and sample files.

use super::dto::{
    CardQuery, CardsResponse, FileQuery, ReviewCardRequest, SampleFile, SampleText,
    WriteCardRequest,
};
use super::{samples, service as card_workflow};
use crate::app::Shared;
use crate::error::{ApiError, ApiResult, ErrorBody};
use crate::modules::auth::extractor::Annotator;
use crate::shared::clock::now_rfc3339;
use axum::{
    extract::{Query, State},
    Json,
};
use serde_json::Value;
use std::path::PathBuf;

#[utoipa::path(get, path = "/api/cards", tag = "cards", security(("session" = [])),
    responses((status = 200, body = CardsResponse), (status = 401, body = ErrorBody)))]
pub async fn get_cards(State(app): State<Shared>, _: Annotator) -> ApiResult<CardsResponse> {
    let cards = app.cards.skeleton().map_err(ApiError::internal)?;
    let entries = app.cards.entries().map_err(ApiError::internal)?;
    Ok(Json(CardsResponse { cards, entries }))
}

fn require_card(app: &Shared, id: &str) -> Result<(), ApiError> {
    match app.cards.exists(id) {
        Ok(true) => Ok(()),
        Ok(false) => Err(ApiError::BadRequest("unknown card id".into())),
        Err(err) => Err(ApiError::internal(err)),
    }
}

#[utoipa::path(put, path = "/api/cards", tag = "cards", security(("session" = [])), params(CardQuery), request_body = WriteCardRequest,
    responses((status = 200, body = Object), (status = 409, body = ErrorBody), (status = 401, body = ErrorBody)))]
pub async fn put_card(
    State(app): State<Shared>,
    Annotator(annotator): Annotator,
    Query(query): Query<CardQuery>,
    Json(body): Json<WriteCardRequest>,
) -> ApiResult<Value> {
    require_card(&app, &query.id)?;
    let _guard = app
        .write_lock
        .lock()
        .map_err(|e| ApiError::internal(e.to_string()))?;
    let entries = app.cards.entries().map_err(ApiError::internal)?;
    let current = entries.get(&query.id).and_then(Value::as_object);
    let entry = card_workflow::write(
        current,
        &annotator,
        &body.text(),
        body.submit,
        now_rfc3339(),
    )
    .map_err(ApiError::Conflict)?;
    app.cards
        .save(&query.id, entry.clone())
        .map_err(ApiError::internal)?;
    Ok(Json(Value::Object(entry)))
}

#[utoipa::path(put, path = "/api/cards/review", tag = "cards", security(("session" = [])), params(CardQuery), request_body = ReviewCardRequest,
    responses((status = 200, body = Object), (status = 409, body = ErrorBody), (status = 401, body = ErrorBody)))]
pub async fn put_review(
    State(app): State<Shared>,
    Annotator(annotator): Annotator,
    Query(query): Query<CardQuery>,
    Json(body): Json<ReviewCardRequest>,
) -> ApiResult<Value> {
    require_card(&app, &query.id)?;
    let _guard = app
        .write_lock
        .lock()
        .map_err(|e| ApiError::internal(e.to_string()))?;
    let entries = app.cards.entries().map_err(ApiError::internal)?;
    let current = entries.get(&query.id).and_then(Value::as_object);
    let entry = card_workflow::review(current, &annotator, body.approve, &body.note, now_rfc3339())
        .map_err(ApiError::Conflict)?;
    app.cards
        .save(&query.id, entry.clone())
        .map_err(ApiError::internal)?;
    Ok(Json(Value::Object(entry)))
}

fn sample_root(app: &Shared, id: &str) -> Result<PathBuf, ApiError> {
    match app.cards.sample_root(id) {
        Ok(Some(root)) => Ok(root),
        Ok(None) => Err(ApiError::BadRequest("unknown card id".into())),
        Err(err) => Err(ApiError::internal(err)),
    }
}

#[utoipa::path(get, path = "/api/cards/files", tag = "cards", security(("session" = [])), params(CardQuery),
    responses((status = 200, body = Vec<SampleFile>), (status = 401, body = ErrorBody)))]
pub async fn get_files(
    State(app): State<Shared>,
    _: Annotator,
    Query(query): Query<CardQuery>,
) -> ApiResult<Vec<SampleFile>> {
    let root = sample_root(&app, &query.id)?;
    let files = samples::list(&root)
        .map_err(ApiError::internal)?
        .into_iter()
        .map(|(path, size)| SampleFile { path, size })
        .collect();
    Ok(Json(files))
}

#[utoipa::path(get, path = "/api/cards/file", tag = "cards", security(("session" = [])), params(FileQuery),
    responses((status = 200, body = SampleText), (status = 400, body = ErrorBody), (status = 401, body = ErrorBody)))]
pub async fn get_file(
    State(app): State<Shared>,
    _: Annotator,
    Query(query): Query<FileQuery>,
) -> ApiResult<SampleText> {
    let root = sample_root(&app, &query.id)?;
    let (text, truncated) =
        samples::read(&root, &query.path).map_err(|err| ApiError::BadRequest(err.to_string()))?;
    Ok(Json(SampleText {
        path: query.path,
        text,
        truncated,
    }))
}
