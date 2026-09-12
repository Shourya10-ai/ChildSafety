package com.childsafety.app.data.local.db

import androidx.room.Database
import androidx.room.RoomDatabase

@Database(entities = [], version = 1, exportSchema = true)
abstract class AppDatabase : RoomDatabase() {
    // DAOs will be added in later phases
}
