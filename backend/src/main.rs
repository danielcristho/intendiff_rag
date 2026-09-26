//! HTTP API for the IntentDiff-RAG audit UI.

mod card_routes;
mod cards;
mod clock;
mod samples;
mod store;

use axum::{
    extract::{Query, State},
    http::StatusCode,
    routing::{get, put},
    Json, Router,
};
use clock::now_rfc3339;
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{Arc, Mutex},
};
use store::{valid_annotator, Store};

// Shared by every request handler.
pub(crate) struct App {
    store: Store,
    write_lock: Mutex<()>,
}

pub(crate) type Shared = Arc<App>;
pub(crate) type Failure = (StatusCode, Json<Value>);

pub(crate) fn bad(message: &str) -> Failure {
    (StatusCode::BAD_REQUEST, Json(json!({ "error": message })))
}

pub(crate) fn internal(err: impl std::fmt::Display) -> Failure {
    (
        StatusCode::INTERNAL_SERVER_ERROR,
        Json(json!({ "error": err.to_string() })),
    )
}

// checked_annotator returns the annotator name only if it is safe as a filename.
pub(crate) fn checked_annotator(raw: &str) -> Result<&str, Failure> {
    if valid_annotator(raw) {
        Ok(raw)
    } else {
        Err(bad(
            "invalid annotator: letters, digits, _ or -, at most 32 characters",
        ))
    }
}

#[derive(Deserialize)]
struct AnnotatorParam {
    annotator: String,
}

#[derive(Deserialize)]
struct DecisionParam {
    id: String,
    annotator: String,
}

async fn get_pairs(State(app): State<Shared>) -> Result<Json<Value>, Failure> {
    let (source, pairs) = app.store.pairs().map_err(internal)?;
    Ok(Json(json!({ "source": source, "pairs": pairs })))
}

async fn get_decisions(
    State(app): State<Shared>,
    Query(params): Query<AnnotatorParam>,
) -> Result<Json<Value>, Failure> {
    let annotator = checked_annotator(&params.annotator)?;
    let decisions = app.store.decisions(annotator).map_err(internal)?;
    Ok(Json(Value::Object(decisions)))
}

#[derive(Deserialize)]
struct PairParam {
    pair_id: String,
}

async fn get_results(
    State(app): State<Shared>,
    Query(params): Query<PairParam>,
) -> Result<Json<Value>, Failure> {
    let rows = app.store.results(&params.pair_id).map_err(internal)?;
    Ok(Json(Value::Array(rows)))
}

async fn get_annotators(State(app): State<Shared>) -> Result<Json<Value>, Failure> {
    let rows: Vec<Value> = app
        .store
        .annotators()
        .map_err(internal)?
        .into_iter()
        .map(|(annotator, count)| json!({ "annotator": annotator, "count": count }))
        .collect();
    Ok(Json(Value::Array(rows)))
}

async fn put_decision(
    State(app): State<Shared>,
    Query(params): Query<DecisionParam>,
    Json(patch): Json<Value>,
) -> Result<Json<Value>, Failure> {
    if params.id.trim().is_empty() {
        return Err(bad("id is required"));
    }
    let annotator = checked_annotator(&params.annotator)?;

    let guard = app.write_lock.lock().map_err(|e| internal(e.to_string()))?;
    let merged = app
        .store
        .merge_decision(annotator, &params.id, &patch, now_rfc3339())
        .map_err(internal)?;
    drop(guard);

    Ok(Json(merged))
}

struct Options {
    data_dir: PathBuf,
    port: u16,
}

fn parse_args(args: &[String]) -> Options {
    let mut options = Options {
        data_dir: PathBuf::from("../data"),
        port: 8000,
    };
    for pair in args.chunks(2) {
        match pair {
            [flag, value] if flag == "--data-dir" => options.data_dir = PathBuf::from(value),
            [flag, value] if flag == "--port" => {
                options.port = value.parse().expect("--port must be a number")
            }
            _ => {}
        }
    }
    options
}

fn routes(app: Shared) -> Router {
    Router::new()
        .route("/api/pairs", get(get_pairs))
        .route("/api/decisions", get(get_decisions))
        .route("/api/decisions", put(put_decision))
        .route("/api/annotators", get(get_annotators))
        .route("/api/results", get(get_results))
        .route("/health", get(|| async { "ok" }))
        .merge(card_routes::routes())
        .with_state(app)
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt().with_target(false).init();

    let argv: Vec<String> = std::env::args().collect();
    let options = parse_args(&argv[1..]);
    let app = Arc::new(App {
        store: Store::new(options.data_dir.clone()),
        write_lock: Mutex::new(()),
    });

    let addr = format!("0.0.0.0:{}", options.port);
    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .expect("failed to bind");
    tracing::info!(
        "listening on {addr} · data dir {}",
        options.data_dir.display()
    );
    axum::serve(listener, routes(app)).await.unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_annotator_names_that_escape_the_data_dir() {
        assert!(checked_annotator("robby").is_ok());
        assert!(checked_annotator("../../etc/passwd").is_err());
    }

    #[test]
    fn falls_back_to_local_defaults_when_flags_are_absent() {
        let options = parse_args(&[]);
        assert_eq!(options.port, 8000);
        assert_eq!(options.data_dir, PathBuf::from("../data"));

        let given = parse_args(&[
            "--port".into(),
            "9100".into(),
            "--data-dir".into(),
            "/tmp/d".into(),
        ]);
        assert_eq!(given.port, 9100);
        assert_eq!(given.data_dir, PathBuf::from("/tmp/d"));
    }
}
