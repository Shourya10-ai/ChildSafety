package com.childsafety.app.network.models

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

@JsonClass(generateAdapter = true)
data class ChatMessageRequest(
    val content: String,
    @Json(name = "message_type") val messageType: String = "text",
    @Json(name = "media_url") val mediaUrl: String? = null
)

@JsonClass(generateAdapter = true)
data class ChatMessageResponse(
    val id: String,
    @Json(name = "case_id") val caseId: String,
    @Json(name = "sender_id") val senderId: String,
    @Json(name = "sender_role") val senderRole: String,
    @Json(name = "sender_name") val senderName: String? = null,
    val content: String,
    @Json(name = "message_type") val messageType: String = "text",
    @Json(name = "media_url") val mediaUrl: String? = null,
    @Json(name = "is_read") val isRead: Boolean = false,
    @Json(name = "created_at") val createdAt: String
)

@JsonClass(generateAdapter = true)
data class ChatHistoryResponse(
    @Json(name = "case_id") val caseId: String,
    @Json(name = "child_id") val childId: String,
    @Json(name = "protected_case_id") val protectedCaseId: String? = null,
    @Json(name = "assigned_moderator_name") val assignedModeratorName: String? = null,
    val messages: List<ChatMessageResponse> = emptyList(),
    @Json(name = "total_count") val totalCount: Int = 0
)
