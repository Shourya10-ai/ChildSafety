package com.childsafety.app.network

import com.childsafety.app.network.models.ChildCreateRequest
import com.childsafety.app.network.models.ChildResponse
import com.childsafety.app.network.models.LinkChildRequest
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

interface ChildApi {
    @POST("api/v1/children")
    suspend fun createChild(@Body request: ChildCreateRequest): ChildResponse

    @GET("api/v1/children/me")
    suspend fun getMyChildProfile(): ChildResponse

    @GET("api/v1/children/{id}")
    suspend fun getChild(@Path("id") id: String): ChildResponse

    @POST("api/v1/children/link")
    suspend fun linkChild(@Body request: LinkChildRequest): ChildResponse
}
