package com.childsafety.app.data.local.db

import androidx.room.*

@Dao
interface OfflineQueueDao {
    @Insert
    suspend fun insertQueuedReport(report: QueuedReportEntity): Long

    @Query("SELECT * FROM queued_reports WHERE syncStatus = 'PENDING' ORDER BY createdAt ASC")
    suspend fun getPendingReports(): List<QueuedReportEntity>

    @Update
    suspend fun updateReport(report: QueuedReportEntity)

    @Delete
    suspend fun deleteReport(report: QueuedReportEntity)

    @Insert
    suspend fun insertQueuedSos(sos: QueuedSosEntity): Long

    @Query("SELECT * FROM queued_sos WHERE syncStatus = 'PENDING' ORDER BY createdAt ASC")
    suspend fun getPendingSos(): List<QueuedSosEntity>

    @Update
    suspend fun updateSos(sos: QueuedSosEntity)

    @Delete
    suspend fun deleteSos(sos: QueuedSosEntity)
}
