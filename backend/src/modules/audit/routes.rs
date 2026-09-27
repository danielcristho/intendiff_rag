// Audit module routes for the application.

use super::handlers::{
    __path_get_annotators, __path_get_decisions, __path_put_decision, get_annotators,
    get_decisions, put_decision,
};
use crate::app::Shared;
use utoipa_axum::{router::OpenApiRouter, routes};

pub fn routes() -> OpenApiRouter<Shared> {
    OpenApiRouter::new()
        .routes(routes!(get_decisions, put_decision))
        .routes(routes!(get_annotators))
}
