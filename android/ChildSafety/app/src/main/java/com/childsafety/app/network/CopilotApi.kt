package com.childsafety.app.network

import com.childsafety.app.network.models.ChildSafetyChatRequest
import com.childsafety.app.network.models.ChildSafetyChatResponse
import com.childsafety.app.network.models.StatutoryQueryRequest
import com.childsafety.app.network.models.StatutoryQueryResponse
import com.childsafety.app.network.models.VoiceReportResponse
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part

interface CopilotApi {

    @POST("api/v1/copilot/child-safety-chat")
    suspend fun chatWithSafetyGuardian(
        @Body request: ChildSafetyChatRequest
    ): Response<ChildSafetyChatResponse>

    @POST("api/v1/copilot/statutory-query")
    suspend fun queryStatutoryCorpus(
        @Body request: StatutoryQueryRequest
    ): Response<StatutoryQueryResponse>

    @Multipart
    @POST("api/v1/speech/voice-report")
    suspend fun submitVoiceReport(
        @Part file: MultipartBody.Part,
        @Part("platform") platform: RequestBody?,
        @Part("category") category: RequestBody?
    ): Response<VoiceReportResponse>
}
