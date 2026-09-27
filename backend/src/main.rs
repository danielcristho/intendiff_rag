//! Serve the audit API, or run `user-add <username>` to create an account; settings come from .env.

use intentdiff_backend::{
    app::App,
    config::Config,
    modules::auth::{accounts::Accounts, repository::UserRepository},
    router::router,
};
use std::net::SocketAddr;

fn fail(message: &str) -> ! {
    eprintln!("{message}");
    std::process::exit(1)
}

// add_user reads the password from the terminal to keep it out of shell history.
fn add_user(name: Option<&String>, config: &Config) {
    let Some(name) = name else {
        fail("usage: intentdiff-backend user-add <username>");
    };
    let password =
        rpassword::prompt_password("password: ").unwrap_or_else(|e| fail(&e.to_string()));
    let again = rpassword::prompt_password("again: ").unwrap_or_else(|e| fail(&e.to_string()));
    if password != again {
        fail("passwords do not match");
    }
    let accounts = Accounts::new(UserRepository::new(&config.data_dir));
    match accounts.add(name, &password) {
        Ok(()) => println!("saved {name} in {}", config.data_dir.display()),
        Err(err) => fail(&err),
    }
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt().with_target(false).init();
    // A missing .env is fine: docker compose passes the same variables.
    dotenvy::dotenv().ok();
    let config = Config::from_env().unwrap_or_else(|err| fail(&err));

    let argv: Vec<String> = std::env::args().collect();
    if argv.get(1).map(String::as_str) == Some("user-add") {
        return add_user(argv.get(2), &config);
    }

    let app = App::new(&config).unwrap_or_else(|err| fail(&err));
    let routes = router(app, &config).unwrap_or_else(|err| fail(&err));
    let listener = tokio::net::TcpListener::bind(config.listen_addr)
        .await
        .unwrap_or_else(|err| fail(&format!("cannot listen on {}: {err}", config.listen_addr)));
    tracing::info!(
        "listening on {} · data dir {}",
        config.listen_addr,
        config.data_dir.display()
    );
    // The peer address feeds the rate limit when TRUST_PROXY is false.
    axum::serve(
        listener,
        routes.into_make_service_with_connect_info::<SocketAddr>(),
    )
    .await
    .unwrap();
}
