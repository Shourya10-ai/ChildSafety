package com.childsafety.app.ui.child

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.network.MissingChildApi
import com.childsafety.app.network.models.DpdpRightsResponse
import com.childsafety.app.network.models.ErasureRequest
import com.childsafety.app.network.models.ErasureResponse
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DpdpRightsUiState(
    val isLoading: Boolean = false,
    val rights: DpdpRightsResponse? = null,
    val errorMessage: String? = null,
    val isSubmittingErasure: Boolean = false,
    val erasureResult: ErasureResponse? = null
)

@HiltViewModel
class DpdpRightsViewModel @Inject constructor(
    private val missingChildApi: MissingChildApi
) : ViewModel() {

    private val _uiState = MutableStateFlow(DpdpRightsUiState())
    val uiState: StateFlow<DpdpRightsUiState> = _uiState

    init {
        loadRights()
    }

    fun loadRights() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, errorMessage = null)
            try {
                val res = missingChildApi.getDpdpRights()
                if (res.isSuccessful && res.body() != null) {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        rights = res.body()
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        errorMessage = "Could not fetch DPDP rights (${res.code()})"
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    errorMessage = e.localizedMessage ?: "Failed to query DPDP rights registry"
                )
            }
        }
    }

    fun requestErasure(reason: String) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSubmittingErasure = true, errorMessage = null)
            try {
                val res = missingChildApi.submitErasureRequest(ErasureRequest(reason = reason))
                if (res.isSuccessful && res.body() != null) {
                    _uiState.value = _uiState.value.copy(
                        isSubmittingErasure = false,
                        erasureResult = res.body()
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isSubmittingErasure = false,
                        errorMessage = "Erasure request failed (${res.code()})"
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isSubmittingErasure = false,
                    errorMessage = e.localizedMessage ?: "Network error during erasure submission"
                )
            }
        }
    }

    fun clearErasureResult() {
        _uiState.value = _uiState.value.copy(erasureResult = null)
    }
}
