package com.childsafety.app.ui.child

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.network.MissingChildApi
import com.childsafety.app.network.models.MissingChildResponse
import com.childsafety.app.network.models.SightingCreateRequest
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class MissingChildAlertsState(
    val isLoading: Boolean = false,
    val alerts: List<MissingChildResponse> = emptyList(),
    val errorMessage: String? = null,
    val isSubmittingSighting: Boolean = false,
    val sightingSuccessMessage: String? = null
)

@HiltViewModel
class MissingChildAlertsViewModel @Inject constructor(
    private val missingChildApi: MissingChildApi
) : ViewModel() {

    private val _uiState = MutableStateFlow(MissingChildAlertsState())
    val uiState: StateFlow<MissingChildAlertsState> = _uiState

    init {
        loadAlerts()
    }

    fun loadAlerts(state: String? = null, district: String? = null) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)
            try {
                val res = missingChildApi.listActiveMissingChildren(state = state, district = district)
                if (res.isSuccessful && res.body() != null) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        alerts = res.body()!!
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        errorMessage = "Could not load alerts (${res.code()})"
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    errorMessage = e.localizedMessage ?: "Failed to connect to safety network"
                )
            }
        }
    }

    fun submitSighting(
        missingChildId: String,
        locationAddress: String,
        sightingNotes: String,
        imageUrl: String? = null
    ) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSubmittingSighting = true, sightingSuccessMessage = null)
            try {
                val req = SightingCreateRequest(
                    imageUrl = imageUrl,
                    locationAddress = locationAddress,
                    sightingNotes = sightingNotes
                )
                val res = missingChildApi.submitSighting(missingChildId, req)
                if (res.isSuccessful) {
                    _uiState.value = _uiState.value.copy(
                        isSubmittingSighting = false,
                        sightingSuccessMessage = "Sighting submitted! Police and Childline moderators have been alerted."
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isSubmittingSighting = false,
                        errorMessage = "Submission failed (${res.code()})"
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isSubmittingSighting = false,
                    errorMessage = e.localizedMessage ?: "Network error during sighting submission"
                )
            }
        }
    }

    fun clearSightingSuccess() {
        _uiState.value = _uiState.value.copy(sightingSuccessMessage = null)
    }
}
