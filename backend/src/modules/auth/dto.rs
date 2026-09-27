//! Data Transfer Objects for the auth module.

use serde::{Deserialize, Serialize};
use utoipa::ToSchema;

#[derive(Deserialize, ToSchema)]
pub struct LoginRequest {
    pub username: String,
    pub password: String,
}

#[derive(Serialize, ToSchema)]
pub struct SessionResponse {
    pub annotator: String,
    // expires_at is in Unix seconds.
    pub expires_at: u64,
}
