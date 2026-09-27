//! Runtime settings read from the environment, which .env fills in development.

use std::net::SocketAddr;
use std::path::PathBuf;
use std::time::Duration;

pub struct Config {
    pub data_dir: PathBuf,
    pub listen_addr: SocketAddr,
    pub jwt_secret: String,
    pub session: SessionConfig,
    pub cors_origins: Vec<String>,
    pub login_rate: RateConfig,
    pub api_rate: RateConfig,
    pub trust_proxy: bool,
}

pub struct SessionConfig {
    pub ttl: Duration,
    pub secure_cookie: bool,
}

// RateConfig allows `burst` requests and refills one every `refill`.
#[derive(Clone, Copy)]
pub struct RateConfig {
    pub burst: u32,
    pub refill: Duration,
}

impl Config {
    pub fn from_env() -> Result<Self, String> {
        Self::from_lookup(|key| std::env::var(key).ok())
    }

    // from_lookup takes the variable source as a function so tests need no process env.
    pub fn from_lookup(lookup: impl Fn(&str) -> Option<String>) -> Result<Self, String> {
        let get = |key: &str| {
            lookup(key)
                .filter(|v| !v.trim().is_empty())
                .ok_or(format!("{key} is not set"))
        };
        let parse = |key: &str| -> Result<u64, String> {
            get(key)?
                .trim()
                .parse()
                .map_err(|_| format!("{key} must be a whole number"))
        };
        let flag = |key: &str| -> Result<bool, String> {
            match get(key)?.trim() {
                "true" => Ok(true),
                "false" => Ok(false),
                _ => Err(format!("{key} must be true or false")),
            }
        };
        let rate = |prefix: &str| -> Result<RateConfig, String> {
            Ok(RateConfig {
                burst: u32::try_from(parse(&format!("{prefix}_BURST"))?)
                    .map_err(|e| e.to_string())?,
                refill: Duration::from_secs(parse(&format!("{prefix}_REFILL_SECS"))?),
            })
        };

        Ok(Self {
            data_dir: PathBuf::from(get("DATA_DIR")?),
            listen_addr: format!("{}:{}", get("BIND_ADDR")?, get("BACKEND_PORT")?)
                .parse()
                .map_err(|_| {
                    "BIND_ADDR and BACKEND_PORT must form an address like 0.0.0.0:8100".to_string()
                })?,
            jwt_secret: get("JWT_SECRET")?,
            session: SessionConfig {
                ttl: Duration::from_secs(parse("SESSION_TTL_HOURS")? * 3600),
                secure_cookie: flag("COOKIE_SECURE")?,
            },
            cors_origins: get("CORS_ORIGINS")?
                .split(',')
                .map(|origin| origin.trim().to_string())
                .filter(|origin| !origin.is_empty())
                .collect(),
            login_rate: rate("LOGIN_RATE")?,
            api_rate: rate("API_RATE")?,
            trust_proxy: flag("TRUST_PROXY")?,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    fn example() -> HashMap<&'static str, &'static str> {
        HashMap::from([
            ("DATA_DIR", "./data"),
            ("BIND_ADDR", "0.0.0.0"),
            ("BACKEND_PORT", "8100"),
            ("JWT_SECRET", "0123456789abcdef0123456789abcdef"),
            ("SESSION_TTL_HOURS", "168"),
            ("COOKIE_SECURE", "false"),
            (
                "CORS_ORIGINS",
                "http://localhost:5174, http://192.0.2.10:5174",
            ),
            ("LOGIN_RATE_BURST", "5"),
            ("LOGIN_RATE_REFILL_SECS", "12"),
            ("API_RATE_BURST", "120"),
            ("API_RATE_REFILL_SECS", "1"),
            ("TRUST_PROXY", "true"),
        ])
    }

    fn load(vars: &HashMap<&str, &str>) -> Result<Config, String> {
        Config::from_lookup(|key| vars.get(key).map(|v| v.to_string()))
    }

    #[test]
    fn reads_every_setting_from_the_environment() {
        let config = load(&example()).unwrap();
        assert_eq!(config.session.ttl, Duration::from_secs(168 * 3600));
        assert_eq!(
            config.cors_origins,
            vec!["http://localhost:5174", "http://192.0.2.10:5174"]
        );
        assert_eq!(config.login_rate.burst, 5);
        assert_eq!(config.listen_addr.to_string(), "0.0.0.0:8100");
        assert!(config.trust_proxy && !config.session.secure_cookie);
    }

    #[test]
    fn names_the_variable_that_is_missing_or_malformed() {
        for (key, value) in [
            ("JWT_SECRET", ""),
            ("COOKIE_SECURE", "yes"),
            ("LOGIN_RATE_BURST", "five"),
        ] {
            let mut vars = example();
            vars.insert(key, value);
            let error = load(&vars).err().unwrap();
            assert!(error.contains(key), "{error}");
        }
        let mut vars = example();
        vars.remove("CORS_ORIGINS");
        assert!(load(&vars).err().unwrap().contains("CORS_ORIGINS"));
    }
}
