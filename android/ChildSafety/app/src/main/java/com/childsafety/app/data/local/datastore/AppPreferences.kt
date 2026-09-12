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
        val CHILD_PIN = stringPreferencesKey("child_pin")
        val SERVER_URL = stringPreferencesKey("server_url")
    }
    
    val appMode: Flow<String?> = context.dataStore.data.map { it[APP_MODE] }
    val activeProfileId: Flow<String?> = context.dataStore.data.map { it[ACTIVE_PROFILE_ID] }
    val language: Flow<String?> = context.dataStore.data.map { it[LANGUAGE] }
    val isOnboarded: Flow<Boolean> = context.dataStore.data.map { it[IS_ONBOARDED] ?: false }
    val authToken: Flow<String?> = context.dataStore.data.map { it[AUTH_TOKEN] }
    val childPin: Flow<String?> = context.dataStore.data.map { it[CHILD_PIN] }
    val serverUrl: Flow<String?> = context.dataStore.data.map { it[SERVER_URL] }
    
    suspend fun setAppMode(mode: String) {
        context.dataStore.edit { it[APP_MODE] = mode }
    }

    suspend fun setActiveProfileId(profileId: String?) {
        context.dataStore.edit { 
            if (profileId != null) it[ACTIVE_PROFILE_ID] = profileId 
            else it.remove(ACTIVE_PROFILE_ID) 
        }
    }
    
    suspend fun setOnboarded(onboarded: Boolean) {
        context.dataStore.edit { it[IS_ONBOARDED] = onboarded }
    }
    
    suspend fun setLanguage(lang: String) {
        context.dataStore.edit { it[LANGUAGE] = lang }
    }

    suspend fun setAuthToken(token: String) {
        context.dataStore.edit { it[AUTH_TOKEN] = token }
    }

    suspend fun setChildPin(pin: String?) {
        context.dataStore.edit { 
            if (pin != null) it[CHILD_PIN] = pin 
            else it.remove(CHILD_PIN) 
        }
    }

    suspend fun setServerUrl(url: String?) {
        context.dataStore.edit { 
            if (url != null) it[SERVER_URL] = url 
            else it.remove(SERVER_URL) 
        }
    }
    
    suspend fun clear() {
        context.dataStore.edit { it.clear() }
    }
}
