package com.childsafety.app.network

import com.childsafety.app.network.models.*
import retrofit2.Response
import retrofit2.http.*

interface MissingChildApi {

    @POST("api/v1/missing-children/")
    suspend fun reportMissingChild(
        @Body request: MissingChildCreateRequest
    ): Response<MissingChildResponse>

    @GET("api/v1/missing-children/")
    suspend fun listActiveMissingChildren(
        @Query("state") state: String? = null,
        @Query("district") district: String? = null,
        @Query("limit") limit: Int = 50,
        @Query("offset") offset: Int = 0
    ): Response<List<MissingChildResponse>>

    @GET("api/v1/missing-children/{id}")
    suspend fun getMissingChildDetail(
        @Path("id") id: String
    ): Response<MissingChildResponse>

    @POST("api/v1/missing-children/{id}/sightings")
    suspend fun submitSighting(
        @Path("id") id: String,
        @Body request: SightingCreateRequest
    ): Response<SightingResponse>

    @GET("api/v1/dpdp/rights")
    suspend fun getDpdpRights(): Response<DpdpRightsResponse>

    @POST("api/v1/dpdp/erasure-request")
    suspend fun submitErasureRequest(
        @Body request: ErasureRequest
    ): Response<ErasureResponse>
}
