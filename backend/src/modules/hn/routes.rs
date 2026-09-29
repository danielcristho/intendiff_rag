//! HN module routes for the application.

use super::handlers::{
    __path_get_candidate, __path_get_queue, __path_put_verification, get_candidate, get_queue,
    put_verification,
};
use crate::app::Shared;
use utoipa_axum::{router::OpenApiRouter, routes};

pub fn routes() -> OpenApiRouter<Shared> {
    OpenApiRouter::new()
        .routes(routes!(get_queue))
        .routes(routes!(get_candidate))
        .routes(routes!(put_verification))
}
