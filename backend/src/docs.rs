//! OpenAPI document; each module's routes add their own paths to it.

use utoipa::openapi::security::{ApiKey, ApiKeyValue, SecurityScheme};
use utoipa::{Modify, OpenApi};

use crate::modules::auth::cookie::SESSION_COOKIE;

#[derive(OpenApi)]
#[openapi(
    info(title = "IntentDiff-RAG audit API"),
    modifiers(&SessionCookieScheme),
    tags(
        (name = "auth", description = "Login and the session cookie"),
        (name = "pairs", description = "Update pairs and model runs"),
        (name = "audit", description = "Each annotator's own labels"),
        (name = "cards", description = "Knowledge-base cards and their samples"),
    )
)]
pub struct ApiDoc;

struct SessionCookieScheme;

impl Modify for SessionCookieScheme {
    fn modify(&self, openapi: &mut utoipa::openapi::OpenApi) {
        openapi
            .components
            .get_or_insert_with(Default::default)
            .add_security_scheme(
                "session",
                SecurityScheme::ApiKey(ApiKey::Cookie(ApiKeyValue::new(SESSION_COOKIE))),
            );
    }
}
