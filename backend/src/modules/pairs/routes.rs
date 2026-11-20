use super::handlers::{get_pairs, get_results};
use crate::app::Shared;
use axum::{routing::get, Router};

pub fn routes() -> Router<Shared> {
    Router::new()
        .route("/api/pairs", get(get_pairs))
        .route("/api/results", get(get_results))
}
