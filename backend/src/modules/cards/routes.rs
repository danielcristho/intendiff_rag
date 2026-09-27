//! Card module routes for the application.

use super::handlers::{
    __path_get_cards, __path_get_file, __path_get_files, __path_put_card, __path_put_review,
    get_cards, get_file, get_files, put_card, put_review,
};
use crate::app::Shared;
use utoipa_axum::{router::OpenApiRouter, routes};

pub fn routes() -> OpenApiRouter<Shared> {
    OpenApiRouter::new()
        .routes(routes!(get_cards))
        .routes(routes!(put_card))
        .routes(routes!(put_review))
        .routes(routes!(get_files))
        .routes(routes!(get_file))
}
