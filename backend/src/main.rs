//! Serve the audit API: `cargo run -- --data-dir ../data --port 8000`.

use intentdiff_backend::{app::App, router::router};
use std::path::PathBuf;

struct Options {
    data_dir: PathBuf,
    port: u16,
}

fn parse_args(args: &[String]) -> Options {
    let mut options = Options {
        data_dir: PathBuf::from("../data"),
        port: 8000,
    };
    for pair in args.chunks(2) {
        match pair {
            [flag, value] if flag == "--data-dir" => options.data_dir = PathBuf::from(value),
            [flag, value] if flag == "--port" => {
                options.port = value.parse().expect("--port must be a number")
            }
            _ => {}
        }
    }
    options
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt().with_target(false).init();

    let argv: Vec<String> = std::env::args().collect();
    let options = parse_args(&argv[1..]);
    let routes = router(App::new(&options.data_dir));

    let addr = format!("0.0.0.0:{}", options.port);
    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .expect("failed to bind");
    tracing::info!(
        "listening on {addr} · data dir {}",
        options.data_dir.display()
    );
    axum::serve(listener, routes).await.unwrap();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn falls_back_to_local_defaults_when_flags_are_absent() {
        let options = parse_args(&[]);
        assert_eq!(options.port, 8000);
        assert_eq!(options.data_dir, PathBuf::from("../data"));

        let given = parse_args(&[
            "--port".into(),
            "9100".into(),
            "--data-dir".into(),
            "/tmp/d".into(),
        ]);
        assert_eq!(given.port, 9100);
        assert_eq!(given.data_dir, PathBuf::from("/tmp/d"));
    }
}
