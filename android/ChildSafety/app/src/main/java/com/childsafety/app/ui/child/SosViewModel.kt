package com.childsafety.app.ui.child

import android.Manifest
import android.app.Application
import android.content.pm.PackageManager
import android.location.Location
import androidx.core.content.ContextCompat
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.network.SosApi
import com.childsafety.app.network.models.ResolveSosRequest
import com.childsafety.app.network.models.SosEventResponse
import com.childsafety.app.network.models.TriggerSosRequest
import android.content.Context
import android.location.LocationManager
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import dagger.hilt.android.lifecycle.HiltViewModel
import com.childsafety.app.network.ChildApi
import com.childsafety.app.network.IntelligenceApi
import com.childsafety.app.network.models.ChildResponse
import com.childsafety.app.network.models.RiskEvaluationResponse
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import com.childsafety.app.data.local.db.OfflineQueueDao
import com.childsafety.app.data.local.db.QueuedSosEntity
import com.childsafety.app.worker.OfflineSyncWorker
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import javax.inject.Inject
import kotlin.coroutines.resume

@HiltViewModel
class SosViewModel @Inject constructor(
    application: Application,
    private val sosApi: SosApi,
    private val childApi: ChildApi,
    private val intelligenceApi: IntelligenceApi,
    private val offlineQueueDao: OfflineQueueDao
) : AndroidViewModel(application) {

    private val _isCountdownActive = MutableStateFlow(false)
    val isCountdownActive: StateFlow<Boolean> = _isCountdownActive

    private val _countdownSeconds = MutableStateFlow(3)
    val countdownSeconds: StateFlow<Int> = _countdownSeconds

    private val _activeSos = MutableStateFlow<SosEventResponse?>(null)
    val activeSos: StateFlow<SosEventResponse?> = _activeSos

    private val _childProfile = MutableStateFlow<ChildResponse?>(null)
    val childProfile: StateFlow<ChildResponse?> = _childProfile

    private val _riskEvaluation = MutableStateFlow<RiskEvaluationResponse?>(null)
    val riskEvaluation: StateFlow<RiskEvaluationResponse?> = _riskEvaluation

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading

    private val _statusMessage = MutableStateFlow<String?>(null)
    val statusMessage: StateFlow<String?> = _statusMessage

    private var countdownJob: Job? = null

    init {
        checkActiveSos()
        loadChildRisk()
    }

    fun loadChildRisk() {
        viewModelScope.launch {
            try {
                val profile = childApi.getMyChildProfile()
                _childProfile.value = profile
                val riskRes = intelligenceApi.evaluateChildRisk(profile.id)
                if (riskRes.isSuccessful && riskRes.body() != null) {
                    _riskEvaluation.value = riskRes.body()
                }
            } catch (_: Exception) {}
        }
    }

    fun startSosCountdown() {
        if (_activeSos.value != null) return // Already active
        if (_isCountdownActive.value) {
            cancelSosCountdown()
            return
        }

        _isCountdownActive.value = true
        _countdownSeconds.value = 3

        countdownJob?.cancel()
        countdownJob = viewModelScope.launch {
            for (i in 3 downTo 1) {
                _countdownSeconds.value = i
                delay(1000)
            }
            _isCountdownActive.value = false
            triggerSos()
        }
    }

    fun cancelSosCountdown() {
        countdownJob?.cancel()
        countdownJob = null
        _isCountdownActive.value = false
        _countdownSeconds.value = 3
        _statusMessage.value = "SOS Cancelled"
    }

    fun triggerSos() {
        viewModelScope.launch {
            _isLoading.value = true
            _statusMessage.value = "Acquiring GPS & Sending Emergency Alert..."

            val (lat, lng) = getCurrentLocation()

            try {
                val req = TriggerSosRequest(
                    latitude = lat,
                    longitude = lng,
                    accuracy = 10.0f,
                    locationAddress = "Emergency alert from mobile device",
                    message = "🚨 EMERGENCY SOS: Child triggered emergency beacon!"
                )
                val response = sosApi.triggerSos(req)
                if (response.isSuccessful && response.body() != null) {
                    _activeSos.value = response.body()
                    _statusMessage.value = "🚨 EMERGENCY ACTIVE • Guardians & Responders Dispatched"
                } else {
                    _statusMessage.value = "Failed to trigger SOS: ${response.code()}"
                }
            } catch (e: Exception) {
                try {
                    offlineQueueDao.insertQueuedSos(
                        QueuedSosEntity(
                            childId = null,
                            latitude = lat,
                            longitude = lng,
                            accuracy = 10.0f,
                            message = "🚨 EMERGENCY SOS: Queued offline alert"
                        )
                    )
                    OfflineSyncWorker.enqueueSync(getApplication())
                    _statusMessage.value = "⚠️ OFFLINE: Emergency beacon queued locally. Will dispatch immediately upon network reconnection."
                } catch (dbErr: Exception) {
                    _statusMessage.value = "Network error triggering SOS: ${e.localizedMessage}"
                }
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun triggerSilentDuressSos(onSuccess: (() -> Unit)? = null) {
        viewModelScope.launch {
            val (lat, lng) = getCurrentLocation()
            try {
                val req = TriggerSosRequest(
                    latitude = lat,
                    longitude = lng,
                    accuracy = 10.0f,
                    locationAddress = "Discreet duress alert from mobile device",
                    message = "🚨 SILENT DURESS EMERGENCY: Discreet duress trigger activated",
                    isSilentDuress = true,
                    bypassPrimaryGuardians = true
                )
                val response = sosApi.triggerSos(req)
                if (response.isSuccessful && response.body() != null) {
                    _activeSos.value = response.body()
                    onSuccess?.invoke()
                }
            } catch (e: Exception) {
                try {
                    offlineQueueDao.insertQueuedSos(
                        QueuedSosEntity(
                            childId = null,
                            latitude = lat,
                            longitude = lng,
                            accuracy = 10.0f,
                            message = "🚨 SILENT DURESS: Queued offline alert"
                        )
                    )
                    OfflineSyncWorker.enqueueSync(getApplication())
                    onSuccess?.invoke()
                } catch (_: Exception) {}
            }
        }
    }

    fun resolveSos(reason: String = "Resolved by child - Safe now") {
        val current = _activeSos.value ?: return
        viewModelScope.launch {
            _isLoading.value = true
            try {
                val res = sosApi.resolveSos(current.id, ResolveSosRequest(message = reason))
                if (res.isSuccessful) {
                    _activeSos.value = null
                    _statusMessage.value = "✅ Emergency marked SAFE & resolved."
                } else {
                    _statusMessage.value = "Failed to resolve: ${res.code()}"
                }
            } catch (e: Exception) {
                _statusMessage.value = "Error resolving SOS: ${e.localizedMessage}"
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun checkActiveSos() {
        viewModelScope.launch {
            try {
                val res = sosApi.getActiveSos()
                if (res.isSuccessful && !res.body().isNullOrEmpty()) {
                    _activeSos.value = res.body()!!.firstOrNull()
                }
            } catch (_: Exception) {}
        }
    }

    private suspend fun getCurrentLocation(): Pair<Double, Double> {
        val context = getApplication<Application>()
        return try {
            val hasFine = ContextCompat.checkSelfPermission(
                context, Manifest.permission.ACCESS_FINE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED
            val hasCoarse = ContextCompat.checkSelfPermission(
                context, Manifest.permission.ACCESS_COARSE_LOCATION
            ) == PackageManager.PERMISSION_GRANTED

            if (hasFine || hasCoarse) {
                val fusedClient = LocationServices.getFusedLocationProviderClient(context)
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
                    val lm = context.getSystemService(Context.LOCATION_SERVICE) as? LocationManager
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
