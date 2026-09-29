//! Router-level checks: session, identity, rate limits, CORS and the OpenAPI document.

use axum::body::{to_bytes, Body};
use axum::extract::ConnectInfo;
use axum::http::{header, Method, Request, StatusCode};
use axum::Router;
use intentdiff_backend::{app::App, config::Config, router::router};
use serde_json::Value;
use std::collections::HashMap;
use std::net::SocketAddr;
use std::path::{Path, PathBuf};
use tower::ServiceExt;

const ORIGIN: &str = "http://localhost:5174";

fn data_dir() -> PathBuf {
    static SEQ: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
    let n = SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let dir = std::env::temp_dir().join(format!("idr-api-{}-{n}", std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    dir
}

fn config(dir: &Path, login_burst: &str) -> Config {
    let dir = dir.to_string_lossy().into_owned();
    let vars = HashMap::from([
        ("DATA_DIR", dir.as_str()),
        ("BIND_ADDR", "127.0.0.1"),
        ("BACKEND_PORT", "0"),
        ("JWT_SECRET", "0123456789abcdef0123456789abcdef"),
        ("SESSION_TTL_HOURS", "1"),
        ("COOKIE_SECURE", "false"),
        ("CORS_ORIGINS", ORIGIN),
        ("LOGIN_RATE_BURST", login_burst),
        ("LOGIN_RATE_REFILL_SECS", "60"),
        ("API_RATE_BURST", "1000"),
        ("API_RATE_REFILL_SECS", "1"),
        ("TRUST_PROXY", "false"),
    ]);
    Config::from_lookup(|key| vars.get(key).map(|v| v.to_string())).unwrap()
}

struct Server {
    routes: Router,
    app: intentdiff_backend::app::Shared,
}

fn server_in(dir: &Path, login_burst: &str) -> Server {
    let config = config(dir, login_burst);
    let app = App::new(&config).unwrap();
    for (name, password) in [("A", "password-a"), ("B", "password-b")] {
        app.accounts.add(name, password).unwrap();
    }
    Server {
        routes: router(app.clone(), &config).unwrap(),
        app,
    }
}

fn server() -> Server {
    server_in(&data_dir(), "50")
}

struct Reply {
    status: StatusCode,
    headers: axum::http::HeaderMap,
    body: Value,
}

async fn send(
    server: &Server,
    method: Method,
    uri: &str,
    cookie: Option<&str>,
    body: &str,
) -> Reply {
    let mut request = Request::builder()
        .method(method)
        .uri(uri)
        .header(header::CONTENT_TYPE, "application/json")
        .header(header::ORIGIN, ORIGIN);
    if let Some(cookie) = cookie {
        request = request.header(header::COOKIE, cookie);
    }
    let mut request = request.body(Body::from(body.to_string())).unwrap();
    // The rate limit keys on the peer address, which a real listener supplies.
    request
        .extensions_mut()
        .insert(ConnectInfo(SocketAddr::from(([10, 0, 0, 1], 5000))));
    let response = server.routes.clone().oneshot(request).await.unwrap();
    let status = response.status();
    let headers = response.headers().clone();
    let bytes = to_bytes(response.into_body(), usize::MAX).await.unwrap();
    Reply {
        status,
        headers,
        body: serde_json::from_slice(&bytes).unwrap_or(Value::Null),
    }
}

// login returns the "session=<jwt>" pair to send back as a Cookie header.
async fn login(server: &Server, username: &str, password: &str) -> String {
    let body = format!(r#"{{"username":"{username}","password":"{password}"}}"#);
    let reply = send(server, Method::POST, "/api/login", None, &body).await;
    assert_eq!(reply.status, StatusCode::OK, "{}", reply.body);
    let set_cookie = reply.headers[header::SET_COOKIE].to_str().unwrap();
    set_cookie.split(';').next().unwrap().to_string()
}

#[tokio::test]
async fn every_api_route_but_login_and_logout_requires_a_session() {
    let server = server();
    let routes = [
        (Method::GET, "/api/session"),
        (Method::GET, "/api/pairs"),
        (Method::GET, "/api/decisions"),
        (Method::PUT, "/api/decisions?id=p1"),
        (Method::GET, "/api/annotators"),
        (Method::GET, "/api/results?pair_id=p1"),
        (Method::GET, "/api/cards"),
        (Method::PUT, "/api/cards?id=c1"),
        (Method::PUT, "/api/cards/review?id=c1"),
        (Method::GET, "/api/cards/files?id=c1"),
        (Method::GET, "/api/cards/file?id=c1&path=x"),
        (Method::GET, "/api/hn/queue"),
        (Method::GET, "/api/hn/candidate?id=x@1"),
        (Method::PUT, "/api/hn/verification?id=x@1"),
    ];
    for (method, uri) in routes {
        let reply = send(&server, method.clone(), uri, None, "{}").await;
        assert_eq!(reply.status, StatusCode::UNAUTHORIZED, "{method} {uri}");
        let reply = send(&server, method.clone(), uri, Some("session=forged"), "{}").await;
        assert_eq!(
            reply.status,
            StatusCode::UNAUTHORIZED,
            "{method} {uri} with a forged cookie"
        );
    }
}

#[tokio::test]
async fn login_sets_an_http_only_cookie_and_hands_out_no_token() {
    let server = server();
    let reply = send(
        &server,
        Method::POST,
        "/api/login",
        None,
        r#"{"username":"A","password":"password-a"}"#,
    )
    .await;
    let set_cookie = reply.headers[header::SET_COOKIE].to_str().unwrap();
    assert!(
        set_cookie.contains("HttpOnly") && set_cookie.contains("SameSite=Strict"),
        "{set_cookie}"
    );
    assert_eq!(reply.body["annotator"], "A");
    assert!(reply.body.get("token").is_none());

    let wrong = send(
        &server,
        Method::POST,
        "/api/login",
        None,
        r#"{"username":"A","password":"nope-nope"}"#,
    )
    .await;
    assert_eq!(wrong.status, StatusCode::UNAUTHORIZED);
    assert!(wrong.headers.get(header::SET_COOKIE).is_none());
}

#[tokio::test]
async fn the_session_names_its_holder_and_logout_clears_the_cookie() {
    let server = server();
    let cookie = login(&server, "A", "password-a").await;
    let reply = send(&server, Method::GET, "/api/session", Some(&cookie), "").await;
    assert_eq!(reply.body["annotator"], "A");
    assert!(reply.body["expires_at"].as_u64().unwrap() > 0);

    let reply = send(&server, Method::POST, "/api/logout", Some(&cookie), "").await;
    assert_eq!(reply.status, StatusCode::NO_CONTENT);
    assert!(reply.headers[header::SET_COOKIE]
        .to_str()
        .unwrap()
        .contains("Max-Age=0"));
}

#[tokio::test]
async fn a_decision_is_filed_under_the_session_holder_not_a_query_parameter() {
    let server = server();
    let cookie = login(&server, "A", "password-a").await;
    let reply = send(
        &server,
        Method::PUT,
        "/api/decisions?id=p1&annotator=B",
        Some(&cookie),
        r#"{"label":"benign"}"#,
    )
    .await;
    assert_eq!(reply.status, StatusCode::OK);
    assert_eq!(
        server.app.decisions.decisions("A").unwrap()["p1"]["label"],
        "benign"
    );
    assert!(server.app.decisions.decisions("B").unwrap().is_empty());
}

#[tokio::test]
async fn an_annotator_reads_only_their_own_decisions() {
    let server = server();
    let (cookie_a, cookie_b) = (
        login(&server, "A", "password-a").await,
        login(&server, "B", "password-b").await,
    );
    send(
        &server,
        Method::PUT,
        "/api/decisions?id=p1",
        Some(&cookie_a),
        r#"{"label":"malicious"}"#,
    )
    .await;
    let reply = send(&server, Method::GET, "/api/decisions", Some(&cookie_b), "").await;
    assert_eq!(reply.body, serde_json::json!({}));
}

#[tokio::test]
async fn the_card_author_cannot_approve_their_own_card() {
    let dir = data_dir();
    std::fs::write(dir.join("kb.skeleton.jsonl"), "{\"id\":\"c1\"}\n").unwrap();
    let server = server_in(&dir, "50");
    let (cookie_a, cookie_b) = (
        login(&server, "A", "password-a").await,
        login(&server, "B", "password-b").await,
    );

    let card =
        r#"{"intent":"i","behavior_chain":"b","code_excerpt":"c","rationale":"r","submit":true}"#;
    assert_eq!(
        send(
            &server,
            Method::PUT,
            "/api/cards?id=c1",
            Some(&cookie_a),
            card
        )
        .await
        .status,
        StatusCode::OK
    );

    let approve = r#"{"approve":true}"#;
    let own = send(
        &server,
        Method::PUT,
        "/api/cards/review?id=c1",
        Some(&cookie_a),
        approve,
    )
    .await;
    assert_eq!(own.status, StatusCode::CONFLICT);
    let other = send(
        &server,
        Method::PUT,
        "/api/cards/review?id=c1",
        Some(&cookie_b),
        approve,
    )
    .await;
    assert_eq!(other.body["stage"], "approved");
}

#[tokio::test]
async fn login_attempts_beyond_the_burst_are_refused() {
    let server = server_in(&data_dir(), "3");
    let wrong = r#"{"username":"A","password":"nope-nope"}"#;
    for _ in 0..3 {
        let reply = send(&server, Method::POST, "/api/login", None, wrong).await;
        assert_eq!(reply.status, StatusCode::UNAUTHORIZED);
    }
    let reply = send(&server, Method::POST, "/api/login", None, wrong).await;
    assert_eq!(reply.status, StatusCode::TOO_MANY_REQUESTS);
    // The login limit is its own bucket; other routes keep answering.
    let reply = send(&server, Method::GET, "/api/session", None, "").await;
    assert_eq!(reply.status, StatusCode::UNAUTHORIZED);
}

#[tokio::test]
async fn hn_verification_records_the_verifier_and_refuses_an_undocumented_acceptance() {
    let dir = data_dir();
    std::fs::create_dir_all(dir.join("hn")).unwrap();
    std::fs::write(
        dir.join("hn/queue.jsonl"),
        "{\"id\":\"x@1\",\"name\":\"x\",\"queue_position\":1}\n",
    )
    .unwrap();
    let server = server_in(&dir, "50");
    let cookie = login(&server, "A", "password-a").await;

    let bare = r#"{"accept":true,"category":2}"#;
    let reply = send(
        &server,
        Method::PUT,
        "/api/hn/verification?id=x@1",
        Some(&cookie),
        bare,
    )
    .await;
    assert_eq!(reply.status, StatusCode::BAD_REQUEST);

    let documented =
        r#"{"accept":true,"category":2,"doc_source":"readme","doc_ref":"Telemetry section"}"#;
    let reply = send(
        &server,
        Method::PUT,
        "/api/hn/verification?id=x@1",
        Some(&cookie),
        documented,
    )
    .await;
    assert_eq!(reply.body["by"], "A");
    let queue = send(&server, Method::GET, "/api/hn/queue", Some(&cookie), "").await;
    assert_eq!(queue.body["candidates"][0]["id"], "x@1");
    assert_eq!(queue.body["verifications"]["x@1"]["category"], 2);

    let unknown = send(
        &server,
        Method::PUT,
        "/api/hn/verification?id=y@2",
        Some(&cookie),
        documented,
    )
    .await;
    assert_eq!(unknown.status, StatusCode::BAD_REQUEST);
}

#[tokio::test]
async fn cors_admits_the_configured_origin_with_credentials_and_no_other() {
    let server = server();
    let reply = send(&server, Method::GET, "/health", None, "").await;
    assert_eq!(reply.headers[header::ACCESS_CONTROL_ALLOW_ORIGIN], ORIGIN);
    assert_eq!(
        reply.headers[header::ACCESS_CONTROL_ALLOW_CREDENTIALS],
        "true"
    );

    let request = Request::builder()
        .uri("/health")
        .header(header::ORIGIN, "http://evil.example")
        .body(Body::empty())
        .unwrap();
    let response = server.routes.clone().oneshot(request).await.unwrap();
    assert!(response
        .headers()
        .get(header::ACCESS_CONTROL_ALLOW_ORIGIN)
        .is_none());
}

#[tokio::test]
async fn the_openapi_document_lists_every_api_route() {
    let server = server();
    let reply = send(&server, Method::GET, "/api/openapi.json", None, "").await;
    let paths = reply.body["paths"].as_object().unwrap();
    for path in [
        "/api/login",
        "/api/logout",
        "/api/session",
        "/api/pairs",
        "/api/results",
        "/api/decisions",
        "/api/annotators",
        "/api/cards",
        "/api/cards/review",
        "/api/cards/files",
        "/api/cards/file",
        "/api/hn/queue",
        "/api/hn/candidate",
        "/api/hn/verification",
    ] {
        assert!(
            paths.contains_key(path),
            "{path} missing from the OpenAPI document"
        );
    }
    assert!(reply.body["components"]["securitySchemes"]["session"].is_object());
}
