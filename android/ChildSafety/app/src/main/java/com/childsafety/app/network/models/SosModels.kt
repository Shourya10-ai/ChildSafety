package com.childsafety.app.network.models

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class TriggerSosRequest(
    @Json(name = "child_id") val childId: String? = null,
    @Json(name = "latitude") val latitude: Double,
    @Json(name = "longitude") val longitude: Double,
    @Json(name = "accuracy") val accuracy: Float? = null,
    @Json(name = "location_address") val locationAddress: String? = null,
    @Json(name = "message") val message: String? = null
)

@JsonClass(generateAdapter = true)
data class ResolveSosRequest(
    @Json(name = "message") val message: String? = null
)

@JsonClass(generateAdapter = true)
data class SosEventResponse(
    @Json(name = "id") val id: String,
    @Json(name = "child_id") val childId: String,
    @Json(name = "case_id") val caseId: String?,
    @Json(name = "protected_case_id") val protectedCaseId: String?,
    @Json(name = "latitude") val latitude: Double?,
    @Json(name = "longitude") val longitude: Double?,
    @Json(name = "accuracy") val accuracy: Float?,
    @Json(name = "location_address") val locationAddress: String?,
    @Json(name = "status") val status: String,
    @Json(name = "message") val message: String?,
    @Json(name = "child_name") val childName: String?,
    @Json(name = "protected_child_id") val protectedChildId: String?,
    @Json(name = "notified_guardians_count") val notifiedGuardiansCount: Int = 0,
    @Json(name = "created_at") val createdAt: String,
    @Json(name = "resolved_at") val resolvedAt: String? = null
)

@JsonClass(generateAdapter = true)
data class NotificationItem(
    @Json(name = "id") val id: String,
    @Json(name = "notification_type") val notificationType: String,
    @Json(name = "title") val title: String,
    @Json(name = "body") val body: String,
    @Json(name = "is_read") val isRead: Boolean,
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class NotificationListResponse(
    @Json(name = "items") val items: List<NotificationItem>,
    @Json(name = "unread_count") val unreadCount: Int
)
