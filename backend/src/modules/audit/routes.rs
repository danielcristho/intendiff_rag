use super::handlers::{get_annotators, get_decisions, put_decision};
use crate::app::Shared;
use axum::{routing::get, Router};

pub fn routes() -> Router<Shared> {
    Router::new()
        .route("/api/decisions", get(get_decisions).put(put_decision))
        .route("/api/annotators", get(get_annotators))
}
