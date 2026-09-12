package com.childsafety.app.ui.adult

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.network.ReportApi
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AdultAlertsViewModel @Inject constructor(
    private val reportApi: ReportApi
) : ViewModel() {

    private val _alerts = MutableStateFlow<List<Alert>>(emptyList())
    val alerts: StateFlow<List<Alert>> = _alerts

    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading

    init {
        loadAlerts()
    }

    fun loadAlerts() {
        viewModelScope.launch {
            _isLoading.value = true
            val defaultAlerts = listOf(
                Alert("Critical", "SOS Triggered by Leo", "10:32 AM"),
                Alert("High", "Inappropriate Message Blocked", "Yesterday"),
                Alert("Medium", "Device out of safe zone", "Monday")
            )
            try {
                val res = reportApi.getActiveIncidents()
                if (res.isSuccessful && res.body() != null) {
                    val serverIncidents = res.body()!!.map { inc ->
                        val sev = inc.severity.replaceFirstChar { it.uppercase() }
                        val desc = inc.description ?: inc.incidentType.replace("_", " ").replaceFirstChar { it.uppercase() }
                        Alert(sev, desc, inc.createdAt.take(16).replace("T", " "))
                    }
                    _alerts.value = serverIncidents + defaultAlerts
                } else {
                    _alerts.value = defaultAlerts
                }
            } catch (e: Exception) {
                _alerts.value = defaultAlerts
            } finally {
                _isLoading.value = false
            }
        }
    }
}
