package com.childsafety.app.worker

import android.content.Context
import androidx.work.*
import com.childsafety.app.data.local.db.AppDatabase
import com.childsafety.app.network.ReportApi
import com.childsafety.app.network.SosApi
import com.childsafety.app.network.models.CreateReportRequest
import com.childsafety.app.network.models.TriggerSosRequest
import androidx.room.Room
import com.squareup.moshi.Moshi
import com.squareup.moshi.kotlin.reflect.KotlinJsonAdapterFactory
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import com.childsafety.app.security.TokenManager

class OfflineSyncWorker(
    context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        val appContext = applicationContext
        val db = Room.databaseBuilder(
            appContext,
            AppDatabase::class.java,
            "child_safety_db"
        ).fallbackToDestructiveMigration().build()

        val offlineDao = db.offlineQueueDao()

        val tokenManager = TokenManager(appContext)
        val token = tokenManager.getAccessToken()

        // Build standalone client for background work
        val moshi = Moshi.Builder().add(KotlinJsonAdapterFactory()).build()
        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val requestBuilder = chain.request().newBuilder()
                requestBuilder.addHeader("ngrok-skip-browser-warning", "1")
                if (token != null) {
                    requestBuilder.addHeader("Authorization", "Bearer $token")
                }
                chain.proceed(requestBuilder.build())
            }
            .build()
            
        val retrofit = Retrofit.Builder()
            .baseUrl("https://squishier-clunky-neuter.ngrok-free.dev/")
            .client(okHttpClient)
            .addConverterFactory(MoshiConverterFactory.create(moshi))
            .build()

        val reportApi = retrofit.create(ReportApi::class.java)
        val sosApi = retrofit.create(SosApi::class.java)

        var hasFailure = false

        // 1. Drain pending reports
        val pendingReports = offlineDao.getPendingReports()
        for (report in pendingReports) {
            try {
                val req = CreateReportRequest(
                    childId = report.childId,
                    category = report.category,
                    content = report.details,
                    platform = report.platform,
                    isAnonymous = report.isAnonymous
                )
                val response = reportApi.submitReport(req)
                if (response.isSuccessful) {
                    offlineDao.deleteReport(report)
                } else {
                    hasFailure = true
                }
            } catch (e: Exception) {
                hasFailure = true
            }
        }

        // 2. Drain pending SOS alerts
        val pendingSos = offlineDao.getPendingSos()
        for (sos in pendingSos) {
            try {
                val req = TriggerSosRequest(
                    childId = sos.childId,
                    latitude = sos.latitude,
                    longitude = sos.longitude,
                    accuracy = sos.accuracy,
                    locationAddress = "Offline queued emergency alert",
                    message = sos.message ?: "EMERGENCY SOS: Queued offline alert dispatched upon network sync"
                )
                val response = sosApi.triggerSos(req)
                if (response.isSuccessful) {
                    offlineDao.deleteSos(sos)
                } else {
                    hasFailure = true
                }
            } catch (e: Exception) {
                hasFailure = true
            }
        }

        return if (hasFailure) Result.retry() else Result.success()
    }

    companion object {
        private const val WORK_NAME = "offline_child_safety_sync"

        fun enqueueSync(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val syncRequest = OneTimeWorkRequestBuilder<OfflineSyncWorker>()
                .setConstraints(constraints)
                .setBackoffCriteria(
                    BackoffPolicy.EXPONENTIAL,
                    15,
                    java.util.concurrent.TimeUnit.SECONDS
                )
                .build()

            WorkManager.getInstance(context).enqueueUniqueWork(
                WORK_NAME,
                ExistingWorkPolicy.KEEP,
                syncRequest
            )
        }
    }
}
