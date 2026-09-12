package com.childsafety.app.network.models

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class RiskFactorBreakdown(
    @Json(name = "velocity_score") val velocityScore: Double,
    @Json(name = "severity_score") val severityScore: Double,
    @Json(name = "predator_persistence_score") val predatorPersistenceScore: Double,
    @Json(name = "vulnerability_score") val vulnerabilityScore: Double
)

@JsonClass(generateAdapter = true)
data class StatutoryCitation(
    @Json(name = "act") val act: String,
    @Json(name = "section") val section: String,
    @Json(name = "provision") val provision: String,
    @Json(name = "mandatory_action") val mandatoryAction: String
)

@JsonClass(generateAdapter = true)
data class RiskEvaluationResponse(
    @Json(name = "target_type") val targetType: String,
    @Json(name = "target_id") val targetId: String,
    @Json(name = "protected_id") val protectedId: String,
    @Json(name = "composite_risk_score") val compositeRiskScore: Double,
    @Json(name = "threat_tier") val threatTier: String,
    @Json(name = "factors") val factors: RiskFactorBreakdown,
    @Json(name = "statutory_citations") val statutoryCitations: List<StatutoryCitation> = emptyList(),
    @Json(name = "recommended_interventions") val recommendedInterventions: List<String> = emptyList(),
    @Json(name = "evaluated_at") val evaluatedAt: String? = null
)

@JsonClass(generateAdapter = true)
data class CaseSimilarityMatch(
    @Json(name = "target_case_id") val targetCaseId: String,
    @Json(name = "protected_case_id") val protectedCaseId: String,
    @Json(name = "similarity_score") val similarityScore: Double,
    @Json(name = "match_reasons") val matchReasons: List<String> = emptyList(),
    @Json(name = "shared_suspects") val sharedSuspects: List<String> = emptyList(),
    @Json(name = "jurisdiction") val jurisdiction: String? = null
)

@JsonClass(generateAdapter = true)
data class CaseSimilarityResponse(
    @Json(name = "source_case_id") val sourceCaseId: String,
    @Json(name = "top_matches") val topMatches: List<CaseSimilarityMatch> = emptyList(),
    @Json(name = "evaluated_at") val evaluatedAt: String? = null
)

@JsonClass(generateAdapter = true)
data class GraphStatsResponse(
    @Json(name = "total_nodes") val totalNodes: Int,
    @Json(name = "total_edges") val totalEdges: Int,
    @Json(name = "cases_count") val casesCount: Int,
    @Json(name = "suspects_count") val suspectsCount: Int,
    @Json(name = "multi_victim_predators_count") val multiVictimPredatorsCount: Int,
    @Json(name = "generated_at") val generatedAt: String? = null
)
