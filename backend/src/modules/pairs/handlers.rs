use super::dto::{PairQuery, PairsResponse};
use crate::app::Shared;
use crate::error::{ApiError, ApiResult};
use axum::{
    extract::{Query, State},
    Json,
};
use serde_json::Value;

pub async fn get_pairs(State(app): State<Shared>) -> ApiResult<PairsResponse> {
    let (source, pairs) = app.pairs.pairs().map_err(ApiError::internal)?;
    Ok(Json(PairsResponse { source, pairs }))
}

pub async fn get_results(
    State(app): State<Shared>,
    Query(query): Query<PairQuery>,
) -> ApiResult<Vec<Value>> {
    let rows = app
        .pairs
        .results(&query.pair_id)
        .map_err(ApiError::internal)?;
    Ok(Json(rows))
}
