package com.childsafety.app.network

import com.childsafety.app.network.models.CaseSimilarityResponse
import com.childsafety.app.network.models.GraphStatsResponse
import com.childsafety.app.network.models.RiskEvaluationResponse
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface IntelligenceApi {

    @GET("api/v1/risk/case/{case_id}")
    suspend fun evaluateCaseRisk(
        @Path("case_id") caseId: String
    ): Response<RiskEvaluationResponse>

    @GET("api/v1/risk/child/{child_id}")
    suspend fun evaluateChildRisk(
        @Path("child_id") childId: String
    ): Response<RiskEvaluationResponse>

    @POST("api/v1/risk/case/{case_id}/similar")
    suspend fun findSimilarCases(
        @Path("case_id") caseId: String
    ): Response<CaseSimilarityResponse>

    @GET("api/v1/graph/stats")
    suspend fun getGraphStats(): Response<GraphStatsResponse>
}
