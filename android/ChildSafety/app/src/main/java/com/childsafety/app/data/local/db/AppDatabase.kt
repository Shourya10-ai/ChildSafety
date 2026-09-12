package com.childsafety.app.data.local.db

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(
    entities = [
        UserEntity::class,
        QueuedReportEntity::class,
        QueuedSosEntity::class,
        EmergencyContactEntity::class
    ],
    version = 3,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun userDao(): UserDao
    abstract fun offlineQueueDao(): OfflineQueueDao
    abstract fun emergencyContactDao(): EmergencyContactDao
}
