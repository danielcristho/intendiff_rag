//! Router-level checks of the API contract the audit UI depends on.

use axum::body::{to_bytes, Body};
use axum::http::{Method, Request, StatusCode};
use axum::Router;
use intentdiff_backend::{app::App, router::router};
use serde_json::{json, Value};
use std::path::PathBuf;
use tower::ServiceExt;

fn data_dir() -> PathBuf {
    static SEQ: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
    let n = SEQ.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
    let dir = std::env::temp_dir().join(format!("idr-api-{}-{n}", std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    std::fs::create_dir_all(&dir).unwrap();
    dir
}

async fn send(routes: &Router, method: Method, uri: &str, body: Value) -> (StatusCode, Value) {
    let request = Request::builder()
        .method(method)
        .uri(uri)
        .header("content-type", "application/json")
        .body(Body::from(body.to_string()))
        .unwrap();
    let response = routes.clone().oneshot(request).await.unwrap();
    let status = response.status();
    let bytes = to_bytes(response.into_body(), usize::MAX).await.unwrap();
    (
        status,
        serde_json::from_slice(&bytes).unwrap_or(Value::Null),
    )
}

#[tokio::test]
async fn a_saved_decision_reads_back_only_for_its_annotator() {
    let routes = router(App::new(&data_dir()));
    let (status, _) = send(
        &routes,
        Method::PUT,
        "/api/decisions?id=p1&annotator=alice",
        json!({"label": "benign"}),
    )
    .await;
    assert_eq!(status, StatusCode::OK);

    let (_, mine) = send(
        &routes,
        Method::GET,
        "/api/decisions?annotator=alice",
        Value::Null,
    )
    .await;
    assert_eq!(mine["p1"]["label"], "benign");
    let (_, theirs) = send(
        &routes,
        Method::GET,
        "/api/decisions?annotator=bob",
        Value::Null,
    )
    .await;
    assert_eq!(theirs, json!({}));

    let (_, progress) = send(&routes, Method::GET, "/api/annotators", Value::Null).await;
    assert_eq!(progress, json!([{"annotator": "alice", "count": 1}]));
}

#[tokio::test]
async fn an_annotator_name_that_escapes_the_data_dir_is_refused() {
    let routes = router(App::new(&data_dir()));
    let (status, body) = send(
        &routes,
        Method::PUT,
        "/api/decisions?id=p1&annotator=..%2Fetc",
        json!({"label": "benign"}),
    )
    .await;
    assert_eq!(status, StatusCode::BAD_REQUEST);
    assert!(body["error"]
        .as_str()
        .unwrap()
        .contains("invalid annotator"));
}

#[tokio::test]
async fn pairs_report_which_file_they_came_from() {
    let dir = data_dir();
    std::fs::write(dir.join("pairs.sample.jsonl"), "{\"id\":\"a\"}\n").unwrap();
    let routes = router(App::new(&dir));
    let (status, body) = send(&routes, Method::GET, "/api/pairs", Value::Null).await;
    assert_eq!(status, StatusCode::OK);
    assert_eq!(body["source"], "pairs.sample.jsonl");
    assert_eq!(body["pairs"].as_array().unwrap().len(), 1);
}
