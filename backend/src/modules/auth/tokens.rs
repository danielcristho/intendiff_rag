//! JWT-based token issuance and verification for annotators.

use crate::shared::files::valid_annotator;
use jsonwebtoken::{decode, encode, Algorithm, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

pub const MIN_SECRET: usize = 32;

#[derive(Serialize, Deserialize)]
struct Claims {
    sub: String,
    iat: u64,
    exp: u64,
}

pub struct Tokens {
    encoding: EncodingKey,
    decoding: DecodingKey,
    ttl: Duration,
}

// Session is a verified token's holder and its expiry in Unix seconds.
#[derive(Clone)]
pub struct Session {
    pub annotator: String,
    pub expires_at: u64,
}

fn now_secs() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|elapsed| elapsed.as_secs())
        .unwrap_or(0)
}

impl Tokens {
    pub fn new(secret: &str, ttl: Duration) -> Result<Self, String> {
        if secret.len() < MIN_SECRET {
            return Err(format!("JWT_SECRET needs at least {MIN_SECRET} bytes"));
        }
        Ok(Self {
            encoding: EncodingKey::from_secret(secret.as_bytes()),
            decoding: DecodingKey::from_secret(secret.as_bytes()),
            ttl,
        })
    }

    pub fn ttl(&self) -> Duration {
        self.ttl
    }

    pub fn issue(&self, annotator: &str) -> Result<(String, Session), String> {
        let iat = now_secs();
        let claims = Claims {
            sub: annotator.into(),
            iat,
            exp: iat + self.ttl.as_secs(),
        };
        let token = encode(&Header::new(Algorithm::HS256), &claims, &self.encoding)
            .map_err(|e| e.to_string())?;
        Ok((
            token,
            Session {
                annotator: claims.sub,
                expires_at: claims.exp,
            },
        ))
    }

    pub fn verify(&self, token: &str) -> Option<Session> {
        let claims = decode::<Claims>(token, &self.decoding, &Validation::new(Algorithm::HS256))
            .ok()?
            .claims;
        valid_annotator(&claims.sub).then_some(Session {
            annotator: claims.sub,
            expires_at: claims.exp,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const SECRET: &str = "0123456789abcdef0123456789abcdef";
    const TTL: Duration = Duration::from_secs(3600);

    #[test]
    fn a_token_names_the_annotator_it_was_issued_to() {
        let tokens = Tokens::new(SECRET, TTL).unwrap();
        let (token, issued) = tokens.issue("userme").unwrap();
        let session = tokens.verify(&token).unwrap();
        assert_eq!(session.annotator, "userme");
        assert_eq!(session.expires_at, issued.expires_at);
    }

    #[test]
    fn rejects_a_token_signed_with_another_secret() {
        let ours = Tokens::new(SECRET, TTL).unwrap();
        let theirs = Tokens::new("ffffffffffffffffffffffffffffffff", TTL).unwrap();
        assert!(ours.verify(&theirs.issue("userme").unwrap().0).is_none());
    }

    #[test]
    fn rejects_a_tampered_or_garbage_token() {
        let tokens = Tokens::new(SECRET, TTL).unwrap();
        let (token, _) = tokens.issue("userme").unwrap();
        let mut parts: Vec<&str> = token.split('.').collect();
        parts[1] = "eyJzdWIiOiJCIiwiaWF0IjoxLCJleHAiOjk5OTk5OTk5OTl9";
        assert!(tokens.verify(&parts.join(".")).is_none());
        assert!(tokens.verify("not.a.token").is_none());
    }

    #[test]
    fn rejects_an_expired_token() {
        let tokens = Tokens::new(SECRET, TTL).unwrap();
        let claims = Claims {
            sub: "userme".into(),
            iat: 1,
            exp: 2,
        };
        let token = encode(&Header::new(Algorithm::HS256), &claims, &tokens.encoding).unwrap();
        assert!(tokens.verify(&token).is_none());
    }

    #[test]
    fn expires_after_the_configured_lifetime() {
        let tokens = Tokens::new(SECRET, TTL).unwrap();
        let (_, session) = tokens.issue("userme").unwrap();
        let left = session.expires_at - now_secs();
        assert!(
            (TTL.as_secs() - 1..=TTL.as_secs()).contains(&left),
            "{left}"
        );
    }

    #[test]
    fn refuses_a_secret_too_short_to_sign_with() {
        assert!(Tokens::new("short", TTL).is_err());
    }
}
