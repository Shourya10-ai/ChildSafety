package com.childsafety.app.network.models

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class CreateReportRequest(
    @Json(name = "content") val content: String,
    @Json(name = "category") val category: String,
    @Json(name = "platform") val platform: String? = null,
    @Json(name = "is_anonymous") val isAnonymous: Boolean = true,
    @Json(name = "child_id") val childId: String? = null
)

@JsonClass(generateAdapter = true)
data class ReportResponse(
    @Json(name = "report_id") val reportId: String,
    @Json(name = "case_id") val caseId: String?,
    @Json(name = "protected_case_id") val protectedCaseId: String?,
    @Json(name = "status") val status: String,
    @Json(name = "message") val message: String
)

@JsonClass(generateAdapter = true)
data class IncidentItem(
    @Json(name = "id") val id: String,
    @Json(name = "case_id") val caseId: String,
    @Json(name = "incident_type") val incidentType: String,
    @Json(name = "severity") val severity: String,
    @Json(name = "description") val description: String?,
    @Json(name = "trust_level") val trustLevel: String,
    @Json(name = "source") val source: String,
    @Json(name = "is_verified") val isVerified: Boolean,
    @Json(name = "created_at") val createdAt: String
)
