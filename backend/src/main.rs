//! API untuk alat audit IntentDiff-RAG.
//!
//!     cargo run -- --data-dir ../data --port 8000
//!
//! Menggantikan middleware dev di `frontend/vite.config.ts`; frontend
//! mem-proxy `/api` ke sini. Menyajikan file, bukan database: runner Python
//! dan UI membaca-menulis file yang sama.

mod store;

use axum::{
    extract::{Query, State},
    http::StatusCode,
    routing::{get, put},
    Json, Router,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::{Arc, Mutex},
    time::{SystemTime, UNIX_EPOCH},
};
use store::Store;

struct App {
    store: Store,
    /// Menjaga read-modify-write keputusan. Tanpa ini dua klik verdict yang
    /// berdekatan bisa saling menimpa dan satu keputusan hilang diam-diam.
    write_lock: Mutex<()>,
}

type Shared = Arc<App>;

fn internal(err: impl std::fmt::Display) -> (StatusCode, Json<Value>) {
    (
        StatusCode::INTERNAL_SERVER_ERROR,
        Json(json!({ "error": err.to_string() })),
    )
}

async fn get_pairs(State(app): State<Shared>) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let (source, pairs) = app.store.pairs().map_err(internal)?;
    Ok(Json(json!({ "source": source, "pairs": pairs })))
}

async fn get_decisions(State(app): State<Shared>) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    let decisions = app.store.decisions().map_err(internal)?;
    Ok(Json(Value::Object(decisions)))
}

#[derive(Deserialize)]
struct IdParam {
    id: String,
}

async fn put_decision(
    State(app): State<Shared>,
    Query(params): Query<IdParam>,
    Json(patch): Json<Value>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    if params.id.trim().is_empty() {
        return Err((
            StatusCode::BAD_REQUEST,
            Json(json!({ "error": "id wajib" })),
        ));
    }
    let guard = app.write_lock.lock().map_err(|e| internal(e.to_string()))?;
    let merged = app
        .store
        .merge_decision(&params.id, &patch, now_rfc3339())
        .map_err(internal)?;
    drop(guard);
    Ok(Json(merged))
}

/// Timestamp ISO-8601 UTC tanpa menarik dependency tanggal — detik sejak epoch
/// sudah cukup untuk mengurutkan keputusan audit.
fn now_rfc3339() -> String {
    let secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let (days, rem) = (secs / 86_400, secs % 86_400);
    let (h, m, s) = (rem / 3600, (rem % 3600) / 60, rem % 60);
    let (y, mo, d) = civil_from_days(days as i64);
    format!("{y:04}-{mo:02}-{d:02}T{h:02}:{m:02}:{s:02}Z")
}

/// Algoritma civil_from_days Howard Hinnant — konversi hari-sejak-epoch ke
/// tanggal kalender, sudah benar untuk tahun kabisat.
fn civil_from_days(z: i64) -> (i64, u32, u32) {
    let z = z + 719_468;
    let era = z.div_euclid(146_097);
    let doe = z.rem_euclid(146_097);
    let yoe = (doe - doe / 1460 + doe / 36524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = (doy - (153 * mp + 2) / 5 + 1) as u32;
    let m = if mp < 10 { mp + 3 } else { mp - 9 } as u32;
    (if m <= 2 { y + 1 } else { y }, m, d)
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt().with_target(false).init();

    let mut data_dir = PathBuf::from("../data");
    let mut port = 8000u16;
    let args: Vec<String> = std::env::args().collect();
    for pair in args[1..].chunks(2) {
        match pair {
            [flag, value] if flag == "--data-dir" => data_dir = PathBuf::from(value),
            [flag, value] if flag == "--port" => {
                port = value.parse().expect("--port harus angka")
            }
            _ => {}
        }
    }

    let app = Arc::new(App {
        store: Store::new(data_dir.clone()),
        write_lock: Mutex::new(()),
    });

    let router = Router::new()
        .route("/api/pairs", get(get_pairs))
        .route("/api/decisions", get(get_decisions))
        .route("/api/decisions", put(put_decision))
        .route("/health", get(|| async { "ok" }))
        .with_state(app);

    let addr = format!("0.0.0.0:{port}");
    let listener = tokio::net::TcpListener::bind(&addr).await.expect("bind gagal");
    tracing::info!("listening on {addr} · data dir {}", data_dir.display());
    axum::serve(listener, router).await.unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tanggal_epoch_dan_kabisat_benar() {
        assert_eq!(civil_from_days(0), (1970, 1, 1));
        assert_eq!(civil_from_days(59), (1970, 3, 1));
        // 2024 kabisat: 29 Feb harus ada
        assert_eq!(civil_from_days(19_782), (2024, 2, 29));
        assert_eq!(civil_from_days(19_783), (2024, 3, 1));
    }

    #[test]
    fn timestamp_berbentuk_iso() {
        let t = now_rfc3339();
        assert_eq!(t.len(), 20, "{t}");
        assert!(t.ends_with('Z') && t.contains('T'), "{t}");
    }
}
