package com.childsafety.app.network

import com.childsafety.app.network.models.ChatHistoryResponse
import com.childsafety.app.network.models.ChatMessageRequest
import com.childsafety.app.network.models.ChatMessageResponse
import retrofit2.Response
import retrofit2.http.*

interface ChatApi {

    @GET("api/v1/chat/my-case/messages")
    suspend fun getMyActiveChat(
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0
    ): Response<ChatHistoryResponse>

    @POST("api/v1/chat/my-case/messages")
    suspend fun sendMessageToMyCase(
        @Body request: ChatMessageRequest
    ): Response<ChatMessageResponse>

    @GET("api/v1/chat/cases/{caseId}/messages")
    suspend fun getCaseMessages(
        @Path("caseId") caseId: String,
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0
    ): Response<ChatHistoryResponse>

    @POST("api/v1/chat/cases/{caseId}/messages")
    suspend fun sendCaseMessage(
        @Path("caseId") caseId: String,
        @Body request: ChatMessageRequest
    ): Response<ChatMessageResponse>

    @PUT("api/v1/chat/cases/{caseId}/read")
    suspend fun markCaseChatRead(
        @Path("caseId") caseId: String
    ): Response<Map<String, Any>>
}
