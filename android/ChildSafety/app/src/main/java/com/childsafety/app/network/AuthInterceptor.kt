package com.childsafety.app.network

import com.childsafety.app.security.TokenManager
import okhttp3.Interceptor
import okhttp3.Response
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthInterceptor @Inject constructor(
    private val tokenManager: TokenManager
) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokenManager.getAccessToken()
        val builder = chain.request().newBuilder()
            // Required for ngrok public tunnel — prevents HTML interstitial page
            .addHeader("ngrok-skip-browser-warning", "1")

        if (token != null) {
            builder.addHeader("Authorization", "Bearer $token")
        }

        return chain.proceed(builder.build())
    }
}
