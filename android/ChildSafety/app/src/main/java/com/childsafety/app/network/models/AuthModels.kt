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
    @Json(name = "language_preference") val languagePreference: String = "en"
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
    @Json(name = "user_id") val userId: String
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
    @Json(name = "is_active") val isActive: Boolean
)

@JsonClass(generateAdapter = true)
data class UpdateProfileRequest(
    @Json(name = "full_name") val fullName: String? = null,
    val phone: String? = null,
    @Json(name = "language_preference") val languagePreference: String? = null,
    @Json(name = "fcm_token") val fcmToken: String? = null
)
