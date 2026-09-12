package com.childsafety.app.ui.adult

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.network.ChildApi
import com.childsafety.app.network.models.LinkChildRequest
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class LinkChildState {
    object Idle : LinkChildState()
    object Loading : LinkChildState()
    data class Success(val childId: String) : LinkChildState()
    data class Error(val message: String) : LinkChildState()
}

@HiltViewModel
class LinkChildViewModel @Inject constructor(
    private val childApi: ChildApi
) : ViewModel() {

    private val _uiState = MutableStateFlow<LinkChildState>(LinkChildState.Idle)
    val uiState: StateFlow<LinkChildState> = _uiState

    fun linkChild(protectedChildId: String, relationship: String) {
        _uiState.value = LinkChildState.Loading
        viewModelScope.launch {
            try {
                val response = childApi.linkChild(LinkChildRequest(protectedChildId, relationship))
                _uiState.value = LinkChildState.Success(response.id)
            } catch (e: Exception) {
                _uiState.value = LinkChildState.Error(e.message ?: "Failed to link child")
            }
        }
    }
}
