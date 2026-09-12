package com.childsafety.app.network

import com.childsafety.app.network.models.*
import retrofit2.http.*

interface AuthApi {
    @POST("api/v1/auth/register")
    suspend fun register(@Body request: RegisterRequest): TokenResponse

    @POST("api/v1/auth/login")
    suspend fun login(@Body request: LoginRequest): TokenResponse

    @POST("api/v1/auth/refresh")
    suspend fun refresh(@Body request: RefreshRequest): TokenResponse

    @POST("api/v1/auth/logout")
    suspend fun logout(@Body request: RefreshRequest? = null): MessageResponse

    @GET("api/v1/auth/me")
    suspend fun getMe(): UserProfile

    @PUT("api/v1/auth/me")
    suspend fun updateMe(@Body request: UpdateProfileRequest): UserProfile
}
