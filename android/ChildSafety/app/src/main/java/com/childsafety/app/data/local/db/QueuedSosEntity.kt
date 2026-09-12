package com.childsafety.app.data.local.db

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "queued_sos")
data class QueuedSosEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val childId: String?,
    val latitude: Double,
    val longitude: Double,
    val accuracy: Float?,
    val message: String?,
    val createdAt: Long = System.currentTimeMillis(),
    val syncStatus: String = "PENDING"
)
