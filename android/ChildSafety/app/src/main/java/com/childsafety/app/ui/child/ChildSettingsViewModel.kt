package com.childsafety.app.ui.child

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.network.ChildApi
import com.childsafety.app.network.models.NominateAdultRequest
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class NominateState {
    object Idle : NominateState()
    object Loading : NominateState()
    data class Success(val message: String) : NominateState()
    data class Error(val error: String) : NominateState()
}

@HiltViewModel
class ChildSettingsViewModel @Inject constructor(
    private val childApi: ChildApi
) : ViewModel() {

    private val _nominateState = MutableStateFlow<NominateState>(NominateState.Idle)
    val nominateState: StateFlow<NominateState> = _nominateState

    fun nominateTrustedAdult(identifier: String, relationship: String, reason: String?) {
        _nominateState.value = NominateState.Loading
        viewModelScope.launch {
            try {
                val profile = childApi.getMyChildProfile()
                val response = childApi.nominateTrustedAdult(
                    childId = profile.id,
                    request = NominateAdultRequest(
                        adultIdentifier = identifier,
                        relationshipLabel = relationship,
                        reason = reason.takeIf { !it.isNullOrBlank() }
                    )
                )
                _nominateState.value = NominateState.Success(response.message)
            } catch (e: Exception) {
                _nominateState.value = NominateState.Error(e.message ?: "Failed to nominate adult")
            }
        }
    }

    fun resetNominateState() {
        _nominateState.value = NominateState.Idle
    }
}
