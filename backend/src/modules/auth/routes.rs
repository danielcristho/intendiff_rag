//! Auth module routes for the application.

use super::handlers::{__path_login, __path_logout, __path_session, login, logout, session};
use crate::app::Shared;
use crate::layers::RateLimit;
use utoipa_axum::{router::OpenApiRouter, routes};

// routes puts the login limit on /api/login, the target of password guessing.
pub fn routes(login_limit: RateLimit) -> OpenApiRouter<Shared> {
    OpenApiRouter::new()
        .merge(
            OpenApiRouter::new()
                .routes(routes!(login))
                .layer(login_limit),
        )
        .routes(routes!(logout))
        .routes(routes!(session))
}
