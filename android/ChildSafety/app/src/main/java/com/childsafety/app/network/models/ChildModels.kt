package com.childsafety.app.network.models

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ChildCreateRequest(
    @Json(name = "display_name") val displayName: String,
    @Json(name = "age") val age: Int,
    @Json(name = "gender") val gender: String?,
    @Json(name = "language_preference") val languagePreference: String?
)

@JsonClass(generateAdapter = true)
data class ChildResponse(
    @Json(name = "id") val id: String,
    @Json(name = "protected_child_id") val protectedChildId: String,
    @Json(name = "display_name") val displayName: String,
    @Json(name = "age") val age: Int,
    @Json(name = "gender") val gender: String?,
    @Json(name = "language_preference") val languagePreference: String?,
    @Json(name = "is_active") val isActive: Boolean
)

@JsonClass(generateAdapter = true)
data class LinkChildRequest(
    @Json(name = "protected_child_id") val protectedChildId: String,
    @Json(name = "relationship") val relationship: String
)

@JsonClass(generateAdapter = true)
data class AdultResponse(
    @Json(name = "id") val id: String,
    @Json(name = "user_id") val userId: String,
    @Json(name = "phone") val phone: String?,
    @Json(name = "emergency_contacts") val emergencyContacts: List<EmergencyContact>?,
    @Json(name = "address") val address: String?
)

@JsonClass(generateAdapter = true)
data class EmergencyContact(
    @Json(name = "name") val name: String,
    @Json(name = "phone") val phone: String,
    @Json(name = "relationship") val relationship: String,
    @Json(name = "is_primary") val isPrimary: Boolean
)

@JsonClass(generateAdapter = true)
data class NominateAdultRequest(
    @Json(name = "adult_identifier") val adultIdentifier: String,
    @Json(name = "relationship_label") val relationshipLabel: String,
    @Json(name = "reason") val reason: String? = null
)

@JsonClass(generateAdapter = true)
data class NominateAdultResponse(
    @Json(name = "message") val message: String,
    @Json(name = "link_id") val linkId: String,
    @Json(name = "nomination_status") val nominationStatus: String,
    @Json(name = "relationship_label") val relationshipLabel: String?
)

@JsonClass(generateAdapter = true)
data class TrustedAdultItem(
    @Json(name = "link_id") val linkId: String,
    @Json(name = "adult_id") val adultId: String,
    @Json(name = "child_id") val childId: String,
    @Json(name = "adult_name") val adultName: String?,
    @Json(name = "adult_email") val adultEmail: String?,
    @Json(name = "adult_phone") val adultPhone: String?,
    @Json(name = "relationship") val relationship: String,
    @Json(name = "relationship_label") val relationshipLabel: String?,
    @Json(name = "is_alternate_trusted_adult") val isAlternateTrustedAdult: Boolean,
    @Json(name = "nomination_status") val nominationStatus: String,
    @Json(name = "linked_at") val linkedAt: String?,
    @Json(name = "vetted_at") val vettedAt: String?
)
