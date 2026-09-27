//! Extractors for the caller's identity, read from the session cookie.

use super::cookie::SESSION_COOKIE;
use super::tokens::Session;
use crate::app::Shared;
use crate::error::ApiError;
use axum::{extract::FromRequestParts, http::request::Parts};
use axum_extra::extract::CookieJar;

// CurrentSession is the verified session behind the request's cookie.
pub struct CurrentSession(pub Session);

// Annotator is the caller's name from the session, not from a query parameter.
pub struct Annotator(pub String);

impl FromRequestParts<Shared> for CurrentSession {
    type Rejection = ApiError;

    async fn from_request_parts(parts: &mut Parts, app: &Shared) -> Result<Self, ApiError> {
        let jar = CookieJar::from_headers(&parts.headers);
        let token = jar
            .get(SESSION_COOKIE)
            .map(|cookie| cookie.value().to_owned())
            .ok_or(ApiError::Unauthorized("login required"))?;
        app.tokens
            .verify(&token)
            .map(CurrentSession)
            .ok_or(ApiError::Unauthorized(
                "session expired or invalid; log in again",
            ))
    }
}

impl FromRequestParts<Shared> for Annotator {
    type Rejection = ApiError;

    async fn from_request_parts(parts: &mut Parts, app: &Shared) -> Result<Self, ApiError> {
        let CurrentSession(session) = CurrentSession::from_request_parts(parts, app).await?;
        Ok(Annotator(session.annotator))
    }
}
