//! The router module defines the HTTP routes for the backend application, organizing them into a cohesive structure.

use crate::app::Shared;
use crate::config::Config;
use crate::docs::ApiDoc;
use crate::layers::{cors, rate_limit};
use crate::modules::{audit, auth, cards, pairs};
use axum::{routing::get, Router};
use utoipa::OpenApi;
use utoipa_axum::router::OpenApiRouter;
use utoipa_swagger_ui::SwaggerUi;

pub fn router(app: Shared, config: &Config) -> Result<Router, String> {
    let (api, spec) = OpenApiRouter::with_openapi(ApiDoc::openapi())
        .merge(auth::routes::routes(rate_limit(
            config.login_rate,
            config.trust_proxy,
        )?))
        .merge(pairs::routes::routes())
        .merge(audit::routes::routes())
        .merge(cards::routes::routes())
        .layer(rate_limit(config.api_rate, config.trust_proxy)?)
        .split_for_parts();
    Ok(api
        .merge(SwaggerUi::new("/api/docs").url("/api/openapi.json", spec))
        .route("/health", get(|| async { "ok" }))
        .layer(cors(&config.cors_origins)?)
        .with_state(app))
}
