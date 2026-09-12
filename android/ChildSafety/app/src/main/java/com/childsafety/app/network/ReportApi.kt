package com.childsafety.app.network

import com.childsafety.app.network.models.CreateReportRequest
import com.childsafety.app.network.models.IncidentItem
import com.childsafety.app.network.models.ReportResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query

interface ReportApi {
    @POST("api/v1/reports/")
    suspend fun submitReport(
        @Body request: CreateReportRequest
    ): Response<ReportResponse>

    @GET("api/v1/incidents/active")
    suspend fun getActiveIncidents(
        @Query("limit") limit: Int = 50
    ): Response<List<IncidentItem>>
}
