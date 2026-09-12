package com.childsafety.app.data.repository

import com.childsafety.app.network.AuthApi
import com.childsafety.app.network.models.*
import com.childsafety.app.security.TokenManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

sealed class AuthResult<T> {
    data class Success<T>(val data: T) : AuthResult<T>()
    data class Error<T>(val message: String, val code: Int = 0) : AuthResult<T>()
    class Loading<T> : AuthResult<T>()
}

@Singleton
class AuthRepository @Inject constructor(
    private val authApi: AuthApi,
    private val tokenManager: TokenManager
) {
    suspend fun register(request: RegisterRequest): AuthResult<TokenResponse> = withContext(Dispatchers.IO) {
        try {
            val response = authApi.register(request)
            tokenManager.saveTokens(
                response.accessToken,
                response.refreshToken,
                response.userId,
                response.role,
                request.email
            )
            AuthResult.Success(response)
        } catch (e: retrofit2.HttpException) {
            AuthResult.Error("HTTP Error: ${e.message()}", e.code())
        } catch (e: Exception) {
            AuthResult.Error("Network error. Check your connection.")
        }
    }

    suspend fun login(request: LoginRequest): AuthResult<TokenResponse> = withContext(Dispatchers.IO) {
        try {
            val response = authApi.login(request)
            tokenManager.saveTokens(
                response.accessToken,
                response.refreshToken,
                response.userId,
                response.role,
                request.email
            )
            AuthResult.Success(response)
        } catch (e: retrofit2.HttpException) {
            AuthResult.Error("HTTP Error: ${e.message()}", e.code())
        } catch (e: Exception) {
            AuthResult.Error("Network error. Check your connection.")
        }
    }

    suspend fun logout(): AuthResult<MessageResponse> = withContext(Dispatchers.IO) {
        try {
            val refreshToken = tokenManager.getRefreshToken()
            val response = authApi.logout(refreshToken?.let { RefreshRequest(it) })
            tokenManager.clearTokens()
            AuthResult.Success(response)
        } catch (e: retrofit2.HttpException) {
            tokenManager.clearTokens()
            AuthResult.Error("HTTP Error: ${e.message()}", e.code())
        } catch (e: Exception) {
            tokenManager.clearTokens()
            AuthResult.Error("Network error. Check your connection.")
        }
    }

    suspend fun refreshToken(): AuthResult<TokenResponse> = withContext(Dispatchers.IO) {
        val refreshToken = tokenManager.getRefreshToken() ?: return@withContext AuthResult.Error("No refresh token")
        try {
            val response = authApi.refresh(RefreshRequest(refreshToken))
            tokenManager.saveTokens(
                response.accessToken,
                response.refreshToken,
                response.userId,
                response.role,
                tokenManager.getUserEmail() ?: ""
            )
            AuthResult.Success(response)
        } catch (e: retrofit2.HttpException) {
            tokenManager.clearTokens()
            AuthResult.Error("HTTP Error: ${e.message()}", e.code())
        } catch (e: Exception) {
            AuthResult.Error("Network error. Check your connection.")
        }
    }

    suspend fun getProfile(): AuthResult<UserProfile> = withContext(Dispatchers.IO) {
        try {
            val response = authApi.getMe()
            AuthResult.Success(response)
        } catch (e: retrofit2.HttpException) {
            AuthResult.Error("HTTP Error: ${e.message()}", e.code())
        } catch (e: Exception) {
            AuthResult.Error("Network error. Check your connection.")
        }
    }

    fun isLoggedIn(): Boolean = tokenManager.isLoggedIn()

    fun getCurrentRole(): String? = tokenManager.getUserRole()

    fun getCurrentUserId(): String? = tokenManager.getUserId()

    fun clearSession() {
        tokenManager.clearTokens()
    }

    suspend fun reverseGeocode(latitude: Double?, longitude: Double?): AuthResult<ReverseGeocodeResponse> = withContext(Dispatchers.IO) {
        try {
            val response = authApi.reverseGeocode(latitude, longitude)
            AuthResult.Success(response)
        } catch (e: Exception) {
            AuthResult.Error(e.localizedMessage ?: "Failed to resolve coordinates")
        }
    }
}
