package com.childsafety.app.network

import com.childsafety.app.network.models.NotificationListResponse
import com.childsafety.app.network.models.ResolveSosRequest
import com.childsafety.app.network.models.SosEventResponse
import com.childsafety.app.network.models.TriggerSosRequest
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface SosApi {

    @POST("api/v1/sos/trigger")
    suspend fun triggerSos(
        @Body request: TriggerSosRequest
    ): Response<SosEventResponse>

    @PUT("api/v1/sos/{id}/resolve")
    suspend fun resolveSos(
        @Path("id") id: String,
        @Body request: ResolveSosRequest
    ): Response<SosEventResponse>

    @GET("api/v1/sos/active")
    suspend fun getActiveSos(
        @Query("limit") limit: Int = 50
    ): Response<List<SosEventResponse>>

    @GET("api/v1/notifications/")
    suspend fun getMyNotifications(
        @Query("limit") limit: Int = 50
    ): Response<NotificationListResponse>
}
