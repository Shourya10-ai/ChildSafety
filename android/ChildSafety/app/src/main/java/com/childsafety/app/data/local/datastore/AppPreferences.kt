package com.childsafety.app.data.local.datastore

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore by preferencesDataStore(name = "app_preferences")

@Singleton
class AppPreferences @Inject constructor(
    @ApplicationContext private val context: Context
) {
    companion object {
        val APP_MODE = stringPreferencesKey("app_mode") // child, adult, shared
        val ACTIVE_PROFILE_ID = stringPreferencesKey("active_profile_id")
        val LANGUAGE = stringPreferencesKey("language")
        val IS_ONBOARDED = booleanPreferencesKey("is_onboarded")
        val AUTH_TOKEN = stringPreferencesKey("auth_token")
    }
    
    val appMode: Flow<String?> = context.dataStore.data.map { it[APP_MODE] }
    val isOnboarded: Flow<Boolean> = context.dataStore.data.map { it[IS_ONBOARDED] ?: false }
    val authToken: Flow<String?> = context.dataStore.data.map { it[AUTH_TOKEN] }
    
    suspend fun setAppMode(mode: String) {
        context.dataStore.edit { it[APP_MODE] = mode }
    }
    
    suspend fun setOnboarded(onboarded: Boolean) {
        context.dataStore.edit { it[IS_ONBOARDED] = onboarded }
    }
    
    suspend fun setLanguage(language: String) {
        context.dataStore.edit { it[LANGUAGE] = language }
    }

    suspend fun setAuthToken(token: String) {
        context.dataStore.edit { it[AUTH_TOKEN] = token }
    }
    
    suspend fun clear() {
        context.dataStore.edit { it.clear() }
    }
}
