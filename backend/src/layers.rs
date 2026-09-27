//! Tower layers built from Config: CORS and per-client rate limits.

use crate::config::RateConfig;
use axum::http::{header::CONTENT_TYPE, HeaderValue, Method, Request};
use governor::{clock::QuantaInstant, middleware::NoOpMiddleware};
use std::net::IpAddr;
use std::sync::Arc;
use tower_governor::{
    governor::GovernorConfigBuilder,
    key_extractor::{KeyExtractor, PeerIpKeyExtractor, SmartIpKeyExtractor},
    GovernorError, GovernorLayer,
};
use tower_http::cors::CorsLayer;

// ClientIp trusts forwarded headers behind a proxy; a direct client can forge them.
#[derive(Clone, Copy)]
pub struct ClientIp {
    trust_proxy: bool,
}

impl KeyExtractor for ClientIp {
    type Key = IpAddr;

    fn extract<T>(&self, req: &Request<T>) -> Result<IpAddr, GovernorError> {
        if self.trust_proxy {
            SmartIpKeyExtractor.extract(req)
        } else {
            PeerIpKeyExtractor.extract(req)
        }
    }
}

pub type RateLimit = GovernorLayer<ClientIp, NoOpMiddleware<QuantaInstant>>;

pub fn rate_limit(rate: RateConfig, trust_proxy: bool) -> Result<RateLimit, String> {
    let config = GovernorConfigBuilder::default()
        .period(rate.refill)
        .burst_size(rate.burst)
        .key_extractor(ClientIp { trust_proxy })
        .finish()
        .ok_or("rate limit needs a burst and a refill above zero")?;
    Ok(GovernorLayer {
        config: Arc::new(config),
    })
}

// cors allows credentials, so it lists origins instead of a wildcard, which browsers refuse with cookies.
pub fn cors(origins: &[String]) -> Result<CorsLayer, String> {
    let origins = origins
        .iter()
        .map(|origin| {
            origin
                .parse::<HeaderValue>()
                .map_err(|_| format!("CORS_ORIGINS: {origin} is not a valid origin"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok(CorsLayer::new()
        .allow_origin(origins)
        .allow_credentials(true)
        .allow_methods([Method::GET, Method::POST, Method::PUT])
        .allow_headers([CONTENT_TYPE]))
}
