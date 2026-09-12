package com.childsafety.app.network

import com.childsafety.app.network.models.RefreshRequest
import com.childsafety.app.network.models.TokenResponse
import com.childsafety.app.security.TokenManager
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthInterceptor @Inject constructor(
    private val tokenManager: TokenManager
) : Interceptor {
    
    companion object {
        private val lock = Any()
    }

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val builder = request.newBuilder()
            // Required for ngrok public tunnel — prevents HTML interstitial page
            .addHeader("ngrok-skip-browser-warning", "1")

        val token = tokenManager.getAccessToken()
        if (token != null) {
            builder.addHeader("Authorization", "Bearer $token")
        }

        var response = chain.proceed(builder.build())

        if (response.code == 401) {
            response.close()
            
            synchronized(lock) {
                val currentToken = tokenManager.getAccessToken()
                // Check if another thread already refreshed the token
                if (currentToken != null && currentToken != token) {
                    return chain.proceed(
                        request.newBuilder()
                            .addHeader("ngrok-skip-browser-warning", "1")
                            .addHeader("Authorization", "Bearer $currentToken")
                            .build()
                    )
                }

                val refreshToken = tokenManager.getRefreshToken()
                if (refreshToken != null) {
                    val moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build()
                    val refreshJson = moshi.adapter(RefreshRequest::class.java).toJson(RefreshRequest(refreshToken))
                    
                    val refreshRequest = Request.Builder()
                        .url("https://squishier-clunky-neuter.ngrok-free.dev/api/v1/auth/refresh")
                        .post(refreshJson.toRequestBody("application/json".toMediaType()))
                        .build()
                        
                    val refreshClient = OkHttpClient()
                    val refreshResponse = refreshClient.newCall(refreshRequest).execute()
                    
                    if (refreshResponse.isSuccessful) {
                        val bodyString = refreshResponse.body?.string()
                        if (bodyString != null) {
                            val tokenResponse = moshi.adapter(TokenResponse::class.java).fromJson(bodyString)
                            if (tokenResponse != null) {
                                // Save the new tokens
                                tokenManager.saveTokens(
                                    tokenResponse.accessToken,
                                    tokenResponse.refreshToken,
                                    tokenResponse.userId,
                                    tokenResponse.role,
                                    tokenManager.getUserEmail() ?: ""
                                )
                                return chain.proceed(
                                    request.newBuilder()
                                        .addHeader("ngrok-skip-browser-warning", "1")
                                        .addHeader("Authorization", "Bearer ${tokenResponse.accessToken}")
                                        .build()
                                )
                            }
                        }
                    }
                }
                
                // If we get here, refresh failed or no refresh token
                tokenManager.clearTokens()
                // Proceed with original (which will fail 401 again) or return error response
                return chain.proceed(builder.build())
            }
        }

        return response
    }
}
