package com.childsafety.app.data.local.db

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_users")
data class UserEntity(
    @PrimaryKey val id: String,
    val email: String,
    val fullName: String?,
    val role: String,
    val phone: String?,
    val languagePreference: String,
    val isActive: Boolean
)
