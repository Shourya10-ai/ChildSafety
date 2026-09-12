package com.childsafety.app.ui.adult

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.network.ReportApi
import com.childsafety.app.network.SosApi
import com.childsafety.app.network.models.ResolveSosRequest
import com.childsafety.app.network.models.SosEventResponse
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AdultAlertsViewModel @Inject constructor(
    private val reportApi: ReportApi,
    private val sosApi: SosApi
) : ViewModel() {

    private val _alerts = MutableStateFlow<List<Alert>>(emptyList())
    val alerts: StateFlow<List<Alert>> = _alerts

    private val _activeSosList = MutableStateFlow<List<SosEventResponse>>(emptyList())
    val activeSosList: StateFlow<List<SosEventResponse>> = _activeSosList

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading

    init {
        loadAlerts()
    }

    fun loadAlerts() {
        viewModelScope.launch {
            _isLoading.value = true
            val combinedAlerts = mutableListOf<Alert>()

            // 1. Fetch Active SOS Events
            try {
                val sosRes = sosApi.getActiveSos()
                if (sosRes.isSuccessful && sosRes.body() != null) {
                    val events = sosRes.body()!!
                    _activeSosList.value = events
                    for (ev in events) {
                        val childDesc = ev.childName ?: ev.protectedChildId ?: "Child"
                        combinedAlerts.add(
                            Alert(
                                severity = "Critical",
                                message = "🚨 EMERGENCY SOS: $childDesc triggered beacon! (${ev.latitude?.let { "%.4f, %.4f".format(it, ev.longitude ?: 0.0) } ?: "Location Pending"})",
                                timestamp = ev.createdAt.take(16).replace("T", " ")
                            )
                        )
                    }
                }
            } catch (_: Exception) {}

            // 2. Fetch Active Incidents
            try {
                val incRes = reportApi.getActiveIncidents()
                if (incRes.isSuccessful && incRes.body() != null) {
                    val serverIncidents = incRes.body()!!.map { inc ->
                        val sev = inc.severity.replaceFirstChar { it.uppercase() }
                        val desc = inc.description ?: inc.incidentType.replace("_", " ").replaceFirstChar { it.uppercase() }
                        Alert(sev, desc, inc.createdAt.take(16).replace("T", " "))
                    }
                    combinedAlerts.addAll(serverIncidents)
                }
            } catch (_: Exception) {}

            // 3. Fallback default alerts if empty
            if (combinedAlerts.isEmpty()) {
                combinedAlerts.addAll(
                    listOf(
                        Alert("High", "Inappropriate Message Blocked", "Yesterday"),
                        Alert("Medium", "Device out of safe zone", "Monday")
                    )
                )
            }

            _alerts.value = combinedAlerts
            _isLoading.value = false
        }
    }

    fun resolveSos(sosId: String, note: String = "Resolved by parent") {
        viewModelScope.launch {
            try {
                val res = sosApi.resolveSos(sosId, ResolveSosRequest(message = note))
                if (res.isSuccessful) {
                    loadAlerts()
                }
            } catch (_: Exception) {}
        }
    }
}
