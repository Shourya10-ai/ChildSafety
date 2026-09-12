package com.childsafety.app.network.models

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class MissingChildCreateRequest(
    @Json(name = "child_name") val childName: String,
    @Json(name = "photo_url") val photoUrl: String,
    val description: String,
    @Json(name = "age_when_missing") val ageWhenMissing: Int? = null,
    val gender: String? = null,
    @Json(name = "height_cm") val heightCm: Double? = null,
    @Json(name = "weight_kg") val weightKg: Double? = null,
    @Json(name = "clothing_description") val clothingDescription: String? = null,
    @Json(name = "identifying_marks") val identifyingMarks: String? = null,
    @Json(name = "last_known_address") val lastKnownAddress: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val state: String? = null,
    val district: String? = null
)

@JsonClass(generateAdapter = true)
data class MissingChildResponse(
    val id: String,
    @Json(name = "case_id") val caseId: String,
    @Json(name = "child_id") val childId: String? = null,
    @Json(name = "child_name") val childName: String,
    @Json(name = "photo_url") val photoUrl: String,
    val description: String,
    @Json(name = "age_when_missing") val ageWhenMissing: Int? = null,
    val gender: String? = null,
    @Json(name = "height_cm") val heightCm: Double? = null,
    @Json(name = "weight_kg") val weightKg: Double? = null,
    @Json(name = "clothing_description") val clothingDescription: String? = null,
    @Json(name = "identifying_marks") val identifyingMarks: String? = null,
    @Json(name = "last_known_address") val lastKnownAddress: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val state: String? = null,
    val district: String? = null,
    val status: String = "ACTIVE",
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class SightingCreateRequest(
    @Json(name = "image_url") val imageUrl: String? = null,
    @Json(name = "location_address") val locationAddress: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    @Json(name = "sighting_notes") val sightingNotes: String? = null
)

@JsonClass(generateAdapter = true)
data class SightingResponse(
    val id: String,
    @Json(name = "missing_child_id") val missingChildId: String,
    @Json(name = "image_url") val imageUrl: String? = null,
    @Json(name = "similarity_score") val similarityScore: Double? = 0.0,
    @Json(name = "location_address") val locationAddress: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val source: String = "citizen_report",
    @Json(name = "sighting_notes") val sightingNotes: String? = null,
    val status: String = "PENDING_REVIEW",
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class DpdpRightsResponse(
    @Json(name = "user_id") val userId: String,
    val email: String,
    val role: String,
    @Json(name = "is_adult_self_custody") val isAdultSelfCustody: Boolean,
    @Json(name = "active_consent_on_file") val activeConsentOnFile: Boolean,
    @Json(name = "consent_status") val consentStatus: String? = null,
    @Json(name = "eligible_for_erasure") val eligibleForErasure: Boolean,
    @Json(name = "forensic_retention_locked") val forensicRetentionLocked: Boolean,
    @Json(name = "retention_statute") val retentionStatute: String,
    @Json(name = "dpdp_statutory_rights") val dpdpStatutoryRights: List<String> = emptyList()
)

@JsonClass(generateAdapter = true)
data class ErasureRequest(
    val reason: String,
    val scope: String = "ALL_SURVEILLANCE_AND_TRACKING"
)

@JsonClass(generateAdapter = true)
data class ErasureResponse(
    @Json(name = "request_id") val requestId: String,
    @Json(name = "user_id") val userId: String,
    val status: String,
    @Json(name = "submitted_at") val submittedAt: String,
    val notes: String
)
