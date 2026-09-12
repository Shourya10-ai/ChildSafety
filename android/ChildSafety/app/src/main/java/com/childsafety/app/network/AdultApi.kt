package com.childsafety.app.network

import com.childsafety.app.network.models.AdultResponse
import com.childsafety.app.network.models.ChildResponse
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.PUT

interface AdultApi {
    @GET("api/v1/adults/me")
    suspend fun getAdultProfile(): AdultResponse

    @PUT("api/v1/adults/me")
    suspend fun updateAdultProfile(@Body request: AdultResponse): AdultResponse

    @GET("api/v1/adults/me/children")
    suspend fun getLinkedChildren(): List<ChildResponse>
}
