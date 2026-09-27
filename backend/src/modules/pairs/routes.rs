//! Pairs module routes for the application.

use super::handlers::{__path_get_pairs, __path_get_results, get_pairs, get_results};
use crate::app::Shared;
use utoipa_axum::{router::OpenApiRouter, routes};

pub fn routes() -> OpenApiRouter<Shared> {
    OpenApiRouter::new()
        .routes(routes!(get_pairs))
        .routes(routes!(get_results))
}
