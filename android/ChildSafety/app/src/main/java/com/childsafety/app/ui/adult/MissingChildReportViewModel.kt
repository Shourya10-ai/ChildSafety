package com.childsafety.app.ui.adult

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.network.MissingChildApi
import com.childsafety.app.network.models.MissingChildCreateRequest
import com.childsafety.app.network.models.MissingChildResponse
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class MissingChildReportState(
    val isSubmitting: Boolean = false,
    val successResult: MissingChildResponse? = null,
    val errorMessage: String? = null
)

@HiltViewModel
class MissingChildReportViewModel @Inject constructor(
    private val missingChildApi: MissingChildApi
) : ViewModel() {

    private val _uiState = MutableStateFlow(MissingChildReportState())
    val uiState: StateFlow<MissingChildReportState> = _uiState

    fun reportMissingChild(
        childName: String,
        photoUrl: String,
        description: String,
        age: Int?,
        gender: String?,
        heightCm: Double?,
        clothing: String?,
        identifyingMarks: String?,
        lastKnownAddress: String?,
        state: String?,
        district: String?
    ) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSubmitting = true, errorMessage = null)
            try {
                val req = MissingChildCreateRequest(
                    childName = childName,
                    photoUrl = photoUrl.ifBlank { "https://evidence.storage/missing/default_placeholder.jpg" },
                    description = description,
                    ageWhenMissing = age,
                    gender = gender,
                    heightCm = heightCm,
                    clothingDescription = clothing,
                    identifyingMarks = identifyingMarks,
                    lastKnownAddress = lastKnownAddress,
                    state = state,
                    district = district
                )
                val res = missingChildApi.reportMissingChild(req)
                if (res.isSuccessful && res.body() != null) {
                    _uiState.value = _uiState.value.copy(
                        isSubmitting = false,
                        successResult = res.body()
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isSubmitting = false,
                        errorMessage = "Failed to file report (${res.code()})"
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isSubmitting = false,
                    errorMessage = e.localizedMessage ?: "Network error filing missing child report"
                )
            }
        }
    }

    fun resetState() {
        _uiState.value = MissingChildReportState()
    }
}
