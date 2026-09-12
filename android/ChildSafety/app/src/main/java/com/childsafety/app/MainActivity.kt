package com.childsafety.app

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Location
import android.os.Build
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.view.KeyEvent
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.core.content.ContextCompat
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.lifecycleScope
import com.childsafety.app.data.local.db.OfflineQueueDao
import com.childsafety.app.data.local.db.QueuedSosEntity
import com.childsafety.app.network.SosApi
import com.childsafety.app.network.models.TriggerSosRequest
import com.childsafety.app.security.DuressKeyTrigger
import com.childsafety.app.security.TokenManager
import com.childsafety.app.ui.navigation.AppNavGraph
import com.childsafety.app.ui.navigation.Routes
import com.childsafety.app.ui.theme.ChildSafetyTheme
import com.childsafety.app.worker.OfflineSyncWorker
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import android.location.LocationManager
import android.content.Context
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import javax.inject.Inject
import kotlin.coroutines.resume

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject lateinit var tokenManager: TokenManager
    @Inject lateinit var sosApi: SosApi
    @Inject lateinit var offlineQueueDao: OfflineQueueDao

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)

        // Register callback for discreet duress trigger (e.g. 3x volume-down)
        DuressKeyTrigger.setCallback {
            triggerSilentDuressSos()
        }

        enableEdgeToEdge()
        setContent {
            ChildSafetyTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val startDestination = if (tokenManager.isLoggedIn()) {
                        Routes.MODE_SELECTION
                    } else {
                        Routes.WELCOME
                    }
                    AppNavGraph(startDestination = startDestination)
                }
            }
        }
    }

    override fun onKeyDown(keyCode: Int, event: KeyEvent?): Boolean {
        if (DuressKeyTrigger.handleKeyEvent(keyCode)) {
            triggerSilentDuressSos()
            return true
        }
        return super.onKeyDown(keyCode, event)
    }

    private fun triggerSilentDuressSos() {
        // Discreet haptic feedback to confirm trigger without visual screen change
        provideHapticFeedback()

        lifecycleScope.launch(Dispatchers.IO) {
            val (lat, lng) = getDeviceLocation()
            try {
                val req = TriggerSosRequest(
                    latitude = lat,
                    longitude = lng,
                    accuracy = 10.0f,
                    locationAddress = "Discreet hardware duress trigger",
                    message = "🚨 SILENT DURESS: Hardware trigger activated (Volume-down 3x)",
                    isSilentDuress = true,
                    bypassPrimaryGuardians = true
                )
                sosApi.triggerSos(req)
            } catch (e: Exception) {
                try {
                    offlineQueueDao.insertQueuedSos(
                        QueuedSosEntity(
                            childId = null,
                            latitude = lat,
                            longitude = lng,
                            accuracy = 10.0f,
                            message = "🚨 SILENT DURESS: Queued offline alert (Hardware trigger)"
                        )
                    )
                    OfflineSyncWorker.enqueueSync(applicationContext)
                } catch (_: Exception) {}
            }
        }
    }

    private fun provideHapticFeedback() {
        try {
            val vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                vibratorManager?.defaultVibrator
            } else {
                @Suppress("DEPRECATION")
                getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            }

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                vibrator?.vibrate(VibrationEffect.createOneShot(120, VibrationEffect.DEFAULT_AMPLITUDE))
            } else {
                @Suppress("DEPRECATION")
                vibrator?.vibrate(120)
            }
        } catch (_: Exception) {}
    }

    private suspend fun getDeviceLocation(): Pair<Double, Double> {
        return try {
            val hasFine = ContextCompat.checkSelfPermission(
                this, Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED
            val hasCoarse = ContextCompat.checkSelfPermission(
                this, Manifest.permission.ACCESS_COARSE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED

            if (hasFine || hasCoarse) {
                val fusedClient = LocationServices.getFusedLocationProviderClient(this)
                val location = suspendCancellableCoroutine<Location?> { cont ->
                    val cts = CancellationTokenSource()
                    fusedClient.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, cts.token)
                        .addOnSuccessListener { liveLoc ->
                            if (liveLoc != null) {
                                if (cont.isActive) cont.resume(liveLoc)
                            } else {
                                fusedClient.lastLocation
                                    .addOnSuccessListener { lastLoc ->
                                        if (cont.isActive) cont.resume(lastLoc)
                                    }
                                    .addOnFailureListener {
                                        if (cont.isActive) cont.resume(null)
                                    }
                            }
                        }
                        .addOnFailureListener {
                            fusedClient.lastLocation
                                .addOnSuccessListener { lastLoc ->
                                    if (cont.isActive) cont.resume(lastLoc)
                                }
                                .addOnFailureListener {
                                    if (cont.isActive) cont.resume(null)
                                }
                        }
                } ?: run {
                    val lm = getSystemService(Context.LOCATION_SERVICE) as? LocationManager
                    try {
                        lm?.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
                            ?: lm?.getLastKnownLocation(LocationManager.GPS_PROVIDER)
                    } catch (_: SecurityException) { null }
                }
                if (location != null) {
                    Pair(location.latitude, location.longitude)
                } else {
                    Pair(15.4909, 73.8278)
                }
            } else {
                Pair(15.4909, 73.8278)
            }
        } catch (e: Exception) {
            Pair(15.4909, 73.8278)
        }
    }
}
