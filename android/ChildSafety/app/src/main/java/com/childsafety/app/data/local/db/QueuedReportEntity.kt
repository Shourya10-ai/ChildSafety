package com.childsafety.app.data.local.db

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "queued_reports")
data class QueuedReportEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val childId: String?,
    val category: String,
    val details: String,
    val platform: String?,
    val isAnonymous: Boolean,
    val createdAt: Long = System.currentTimeMillis(),
    val syncStatus: String = "PENDING" // PENDING, SYNCING, SYNCED, FAILED
)
