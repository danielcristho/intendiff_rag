//! Pairs module handlers: HTTP endpoints for knowledge-base pairs and their results.

use super::dto::{PairQuery, PairsResponse};
use crate::app::Shared;
use crate::error::{ApiError, ApiResult, ErrorBody};
use crate::modules::auth::extractor::Annotator;
use axum::{
    extract::{Query, State},
    Json,
};
use serde_json::Value;

#[utoipa::path(get, path = "/api/pairs", tag = "pairs", security(("session" = [])),
    responses((status = 200, body = PairsResponse), (status = 401, body = ErrorBody)))]
pub async fn get_pairs(State(app): State<Shared>, _: Annotator) -> ApiResult<PairsResponse> {
    let (source, pairs) = app.pairs.pairs().map_err(ApiError::internal)?;
    Ok(Json(PairsResponse { source, pairs }))
}

#[utoipa::path(get, path = "/api/results", tag = "pairs", security(("session" = [])), params(PairQuery),
    responses((status = 200, body = Vec<Object>), (status = 401, body = ErrorBody)))]
pub async fn get_results(
    State(app): State<Shared>,
    _: Annotator,
    Query(query): Query<PairQuery>,
) -> ApiResult<Vec<Value>> {
    Ok(Json(
        app.pairs
            .results(&query.pair_id)
            .map_err(ApiError::internal)?,
    ))
}
