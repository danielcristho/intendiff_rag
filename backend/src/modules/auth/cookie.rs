//! The session cookie that carries the JWT, out of reach of page scripts.

use crate::config::SessionConfig;
use axum_extra::extract::cookie::{Cookie, SameSite};
use std::time::Duration;

pub const SESSION_COOKIE: &str = "session";

#[derive(Clone, Copy)]
pub struct SessionCookie {
    secure: bool,
    ttl: Duration,
}

impl SessionCookie {
    pub fn new(config: &SessionConfig) -> Self {
        Self {
            secure: config.secure_cookie,
            ttl: config.ttl,
        }
    }

    pub fn issue(&self, token: String) -> Cookie<'static> {
        self.base(token, self.ttl)
    }

    pub fn clear(&self) -> Cookie<'static> {
        self.base(String::new(), Duration::ZERO)
    }

    fn base(&self, value: String, max_age: Duration) -> Cookie<'static> {
        Cookie::build((SESSION_COOKIE, value))
            .path("/")
            .http_only(true)
            .secure(self.secure)
            .same_site(SameSite::Strict)
            .max_age(max_age.try_into().unwrap_or_default())
            .build()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn cookies(secure: bool) -> SessionCookie {
        SessionCookie::new(&SessionConfig {
            ttl: Duration::from_secs(3600),
            secure_cookie: secure,
        })
    }

    #[test]
    fn keeps_the_token_away_from_scripts_and_other_sites() {
        let text = cookies(true).issue("t".into()).to_string();
        for part in [
            "session=t",
            "HttpOnly",
            "SameSite=Strict",
            "Secure",
            "Max-Age=3600",
            "Path=/",
        ] {
            assert!(text.contains(part), "{text} lacks {part}");
        }
    }

    #[test]
    fn drops_secure_when_the_site_is_served_over_http() {
        assert!(!cookies(false)
            .issue("t".into())
            .to_string()
            .contains("Secure"));
    }

    #[test]
    fn logout_expires_the_cookie_at_once() {
        let text = cookies(true).clear().to_string();
        assert!(
            text.contains("session=;") && text.contains("Max-Age=0"),
            "{text}"
        );
    }
}
