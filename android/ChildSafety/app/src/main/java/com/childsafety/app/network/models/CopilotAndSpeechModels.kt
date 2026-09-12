package com.childsafety.app.network.models

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class StatutoryCitationModel(
    @Json(name = "statute_name") val statuteName: String,
    @Json(name = "section") val section: String,
    @Json(name = "title") val title: String,
    @Json(name = "relevance_summary") val relevanceSummary: String,
    @Json(name = "mandatory_reporting") val mandatoryReporting: Boolean = false,
    @Json(name = "reporting_timeline_hours") val reportingTimelineHours: Int? = null,
    @Json(name = "reporting_authority") val reportingAuthority: String? = null
)

@JsonClass(generateAdapter = true)
data class StatutoryQueryRequest(
    @Json(name = "query_text") val queryText: String,
    @Json(name = "incident_type") val incidentType: String? = "other",
    @Json(name = "child_state") val childState: String? = null,
    @Json(name = "child_district") val childDistrict: String? = null
)

@JsonClass(generateAdapter = true)
data class StatutoryQueryResponse(
    @Json(name = "query") val query: String,
    @Json(name = "grounded_guidance") val groundedGuidance: String,
    @Json(name = "statutory_citations") val statutoryCitations: List<StatutoryCitationModel> = emptyList(),
    @Json(name = "mandatory_reporting_required") val mandatoryReportingRequired: Boolean = false,
    @Json(name = "reporting_authority") val reportingAuthority: String? = null,
    @Json(name = "reporting_timeline_hours") val reportingTimelineHours: Int? = null,
    @Json(name = "statutory_grounded") val statutoryGrounded: Boolean = true,
    @Json(name = "confidence_score") val confidenceScore: Double = 0.95
)

@JsonClass(generateAdapter = true)
data class ChildSafetyChatMessage(
    @Json(name = "sender") val sender: String,
    @Json(name = "message") val message: String,
    @Json(name = "timestamp") val timestamp: String? = null
)

@JsonClass(generateAdapter = true)
data class ChildSafetyChatRequest(
    @Json(name = "message") val message: String,
    @Json(name = "history") val history: List<ChildSafetyChatMessage> = emptyList(),
    @Json(name = "child_id") val childId: String? = null
)

@JsonClass(generateAdapter = true)
data class ChildSafetyChatResponse(
    @Json(name = "reply") val reply: String,
    @Json(name = "detected_threat") val detectedThreat: Boolean = false,
    @Json(name = "distress_level") val distressLevel: String = "NONE",
    @Json(name = "is_emergency") val isEmergency: Boolean = false,
    @Json(name = "suggest_sos") val suggestSos: Boolean = false,
    @Json(name = "suggest_moderator_transfer") val suggestModeratorTransfer: Boolean = false,
    @Json(name = "reassurance_note") val reassuranceNote: String = "",
    @Json(name = "created_at") val createdAt: String? = null
)

@JsonClass(generateAdapter = true)
data class TranscriptionResponse(
    @Json(name = "audio_filename") val audioFilename: String,
    @Json(name = "duration_seconds") val durationSeconds: Double,
    @Json(name = "transcript") val transcript: String,
    @Json(name = "detected_language") val detectedLanguage: String = "en",
    @Json(name = "detected_safety_keywords") val detectedSafetyKeywords: List<String> = emptyList(),
    @Json(name = "detected_threat_level") val detectedThreatLevel: String = "LOW",
    @Json(name = "confidence_score") val confidenceScore: Double = 0.95
)

@JsonClass(generateAdapter = true)
data class VoiceReportResponse(
    @Json(name = "report_id") val reportId: String,
    @Json(name = "case_id") val caseId: String? = null,
    @Json(name = "protected_case_id") val protectedCaseId: String? = null,
    @Json(name = "transcript") val transcript: String,
    @Json(name = "category") val category: String,
    @Json(name = "severity") val severity: String,
    @Json(name = "status") val status: String,
    @Json(name = "message") val message: String,
    @Json(name = "created_at") val createdAt: String? = null
)
