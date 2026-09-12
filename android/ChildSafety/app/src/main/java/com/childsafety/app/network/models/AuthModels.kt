package com.childsafety.app.network.models

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class RegisterRequest(
    val email: String,
    val password: String,
    @Json(name = "full_name") val fullName: String,
    val role: String,
    val phone: String? = null,
    @Json(name = "language_preference") val languagePreference: String = "en",
    val state: String? = null,
    val district: String? = null,
    @Json(name = "pin_code") val pinCode: String? = null,
    @Json(name = "date_of_birth") val dateOfBirth: String? = null,
    @Json(name = "setup_path") val setupPath: String? = null,
    @Json(name = "school_name") val schoolName: String? = null,
    @Json(name = "linked_via_adult_email") val linkedViaAdultEmail: String? = null,
    @Json(name = "relationship_to_child") val relationshipToChild: String? = null,
    val address: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null
)

@JsonClass(generateAdapter = true)
data class ReverseGeocodeResponse(
    val state: String,
    val district: String,
    @Json(name = "pin_code") val pinCode: String? = null,
    val latitude: Double,
    val longitude: Double,
    @Json(name = "state_code") val stateCode: String? = null,
    @Json(name = "district_code") val districtCode: String? = null
)

@JsonClass(generateAdapter = true)
data class LoginRequest(
    val email: String,
    val password: String
)

@JsonClass(generateAdapter = true)
data class TokenResponse(
    @Json(name = "access_token") val accessToken: String,
    @Json(name = "refresh_token") val refreshToken: String,
    @Json(name = "token_type") val tokenType: String,
    val role: String,
    @Json(name = "user_id") val userId: String,
    @Json(name = "protected_child_id") val protectedChildId: String? = null,
    @Json(name = "is_domestic_safety_mode") val isDomesticSafetyMode: Boolean? = null,
    @Json(name = "setup_path") val setupPath: String? = null,
    val state: String? = null,
    val district: String? = null
)

@JsonClass(generateAdapter = true)
data class RefreshRequest(
    @Json(name = "refresh_token") val refreshToken: String
)

@JsonClass(generateAdapter = true)
data class MessageResponse(
    val message: String
)

@JsonClass(generateAdapter = true)
data class UserProfile(
    val id: String,
    val email: String,
    @Json(name = "full_name") val fullName: String?,
    val role: String,
    val phone: String?,
    @Json(name = "language_preference") val languagePreference: String,
    @Json(name = "is_active") val isActive: Boolean,
    val state: String? = null,
    val district: String? = null,
    @Json(name = "pin_code") val pinCode: String? = null,
    @Json(name = "protected_child_id") val protectedChildId: String? = null,
    @Json(name = "is_domestic_safety_mode") val isDomesticSafetyMode: Boolean? = null,
    @Json(name = "setup_path") val setupPath: String? = null
)

@JsonClass(generateAdapter = true)
data class UpdateProfileRequest(
    @Json(name = "full_name") val fullName: String? = null,
    val phone: String? = null,
    @Json(name = "language_preference") val languagePreference: String? = null,
    @Json(name = "fcm_token") val fcmToken: String? = null
)
