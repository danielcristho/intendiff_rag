// HTTP handlers for writing and checking knowledge-base cards.

use crate::clock::now_rfc3339;
use crate::{bad, cards, checked_annotator, internal, samples, Failure, Shared};
use axum::{
    extract::{Query, State},
    http::StatusCode,
    routing::{get, put},
    Json, Router,
};
use serde::Deserialize;
use serde_json::{json, Map, Value};
use std::path::PathBuf;

fn conflict(message: String) -> Failure {
    (StatusCode::CONFLICT, Json(json!({ "error": message })))
}

#[derive(Deserialize)]
struct CardParam {
    id: String,
}

#[derive(Deserialize)]
struct EditParam {
    id: String,
    annotator: String,
}

#[derive(Deserialize)]
struct FileParam {
    id: String,
    path: String,
}

#[derive(Deserialize)]
struct WriteBody {
    #[serde(flatten)]
    text: Map<String, Value>,
    #[serde(default)]
    submit: bool,
}

#[derive(Deserialize)]
struct ReviewBody {
    approve: bool,
    #[serde(default)]
    note: String,
}

async fn get_cards(State(app): State<Shared>) -> Result<Json<Value>, Failure> {
    let skeleton = app.store.kb_skeleton().map_err(internal)?;
    let entries = app.store.card_entries().map_err(internal)?;
    Ok(Json(json!({ "cards": skeleton, "entries": entries })))
}

// A write for an id missing from the skeleton would never reach kb.jsonl.
fn known_card(app: &Shared, id: &str) -> Result<(), Failure> {
    let skeleton = app.store.kb_skeleton().map_err(internal)?;
    if skeleton
        .iter()
        .any(|row| row.get("id").and_then(Value::as_str) == Some(id))
    {
        Ok(())
    } else {
        Err(bad("unknown card id"))
    }
}

async fn put_card(
    State(app): State<Shared>,
    Query(params): Query<EditParam>,
    Json(body): Json<WriteBody>,
) -> Result<Json<Value>, Failure> {
    let annotator = checked_annotator(&params.annotator)?;
    known_card(&app, &params.id)?;

    let _guard = app.write_lock.lock().map_err(|e| internal(e.to_string()))?;
    let entries = app.store.card_entries().map_err(internal)?;
    let current = entries.get(&params.id).and_then(Value::as_object);
    let entry = cards::write(current, annotator, &body.text, body.submit, now_rfc3339())
        .map_err(conflict)?;
    app.store
        .save_card(&params.id, entry.clone())
        .map_err(internal)?;
    Ok(Json(Value::Object(entry)))
}

async fn put_review(
    State(app): State<Shared>,
    Query(params): Query<EditParam>,
    Json(body): Json<ReviewBody>,
) -> Result<Json<Value>, Failure> {
    let annotator = checked_annotator(&params.annotator)?;
    known_card(&app, &params.id)?;

    let _guard = app.write_lock.lock().map_err(|e| internal(e.to_string()))?;
    let entries = app.store.card_entries().map_err(internal)?;
    let current = entries.get(&params.id).and_then(Value::as_object);
    let entry = cards::review(current, annotator, body.approve, &body.note, now_rfc3339())
        .map_err(conflict)?;
    app.store
        .save_card(&params.id, entry.clone())
        .map_err(internal)?;
    Ok(Json(Value::Object(entry)))
}

fn sample_root(app: &Shared, id: &str) -> Result<PathBuf, Failure> {
    match app.store.card_root(id) {
        Ok(Some(root)) => Ok(root),
        Ok(None) => Err(bad("unknown card id")),
        Err(err) => Err(internal(err)),
    }
}

async fn get_files(
    State(app): State<Shared>,
    Query(params): Query<CardParam>,
) -> Result<Json<Value>, Failure> {
    let root = sample_root(&app, &params.id)?;
    let rows: Vec<Value> = samples::list(&root)
        .map_err(internal)?
        .into_iter()
        .map(|(path, size)| json!({ "path": path, "size": size }))
        .collect();
    Ok(Json(Value::Array(rows)))
}

async fn get_file(
    State(app): State<Shared>,
    Query(params): Query<FileParam>,
) -> Result<Json<Value>, Failure> {
    let root = sample_root(&app, &params.id)?;
    let (text, truncated) =
        samples::read(&root, &params.path).map_err(|err| bad(&err.to_string()))?;
    Ok(Json(
        json!({ "path": params.path, "text": text, "truncated": truncated }),
    ))
}

pub fn routes() -> Router<Shared> {
    Router::new()
        .route("/api/cards", get(get_cards).put(put_card))
        .route("/api/cards/review", put(put_review))
        .route("/api/cards/files", get(get_files))
        .route("/api/cards/file", get(get_file))
}
