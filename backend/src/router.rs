use crate::app::Shared;
use crate::modules::{audit, pairs};
use axum::{routing::get, Router};

pub fn router(app: Shared) -> Router {
    Router::new()
        .merge(pairs::routes::routes())
        .merge(audit::routes::routes())
        .route("/health", get(|| async { "ok" }))
        .with_state(app)
}
