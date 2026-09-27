//! Auth handlers: login, logout, and the current session.

use super::dto::{LoginRequest, SessionResponse};
use super::extractor::CurrentSession;
use super::tokens::Session;
use crate::app::Shared;
use crate::error::{ApiError, ErrorBody};
use axum::{extract::State, http::StatusCode, Json};
use axum_extra::extract::CookieJar;

impl From<Session> for SessionResponse {
    fn from(session: Session) -> Self {
        Self {
            annotator: session.annotator,
            expires_at: session.expires_at,
        }
    }
}

// login checks the password and sets the session cookie.
#[utoipa::path(post, path = "/api/login", tag = "auth", request_body = LoginRequest,
    responses((status = 200, body = SessionResponse), (status = 401, body = ErrorBody), (status = 429)))]
pub async fn login(
    State(app): State<Shared>,
    jar: CookieJar,
    Json(body): Json<LoginRequest>,
) -> Result<(CookieJar, Json<SessionResponse>), ApiError> {
    let LoginRequest { username, password } = body;
    let known = tokio::task::spawn_blocking({
        let accounts = app.accounts.clone();
        let username = username.clone();
        move || accounts.verify(&username, &password)
    })
    .await
    .map_err(ApiError::internal)?;
    if !known {
        return Err(ApiError::Unauthorized("wrong username or password"));
    }
    let (token, session) = app.tokens.issue(&username).map_err(ApiError::internal)?;
    Ok((jar.add(app.cookies.issue(token)), Json(session.into())))
}

// logout expires the session cookie.
#[utoipa::path(post, path = "/api/logout", tag = "auth", responses((status = 204)))]
pub async fn logout(State(app): State<Shared>, jar: CookieJar) -> (CookieJar, StatusCode) {
    (jar.add(app.cookies.clear()), StatusCode::NO_CONTENT)
}

// session reports who is logged in and until when.
#[utoipa::path(get, path = "/api/session", tag = "auth", security(("session" = [])),
    responses((status = 200, body = SessionResponse), (status = 401, body = ErrorBody)))]
pub async fn session(CurrentSession(session): CurrentSession) -> Json<SessionResponse> {
    Json(session.into())
}
