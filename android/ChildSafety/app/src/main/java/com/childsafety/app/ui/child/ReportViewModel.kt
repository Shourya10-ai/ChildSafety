package com.childsafety.app.ui.child

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.data.local.db.OfflineQueueDao
import com.childsafety.app.data.local.db.QueuedReportEntity
import com.childsafety.app.network.ReportApi
import com.childsafety.app.network.models.CreateReportRequest
import com.childsafety.app.worker.OfflineSyncWorker
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ReportUiState(
    val isLoading: Boolean = false,
    val isSuccess: Boolean = false,
    val error: String? = null,
    val protectedCaseId: String? = null,
    val message: String? = null
)

@HiltViewModel
class ReportViewModel @Inject constructor(
    application: Application,
    private val reportApi: ReportApi,
    private val offlineQueueDao: OfflineQueueDao
) : AndroidViewModel(application) {

    private val _uiState = MutableStateFlow(ReportUiState())
    val uiState: StateFlow<ReportUiState> = _uiState

    fun submitReport(
        category: String,
        platform: String,
        content: String,
        isAnonymous: Boolean
    ) {
        if (content.isBlank()) {
            _uiState.value = ReportUiState(error = "Please describe what happened.")
            return
        }

        viewModelScope.launch {
            _uiState.value = ReportUiState(isLoading = true)
            val request = CreateReportRequest(
                content = content,
                category = category.ifBlank { "other" },
                platform = platform.ifBlank { null },
                isAnonymous = isAnonymous
            )

            try {
                val response = reportApi.submitReport(request)
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    _uiState.value = ReportUiState(
                        isSuccess = true,
                        protectedCaseId = body.protectedCaseId,
                        message = body.message
                    )
                    return@launch
                }
            } catch (_: Exception) {
                // Network unreachable or server down
            }

            // Offline fallback: store in Room and schedule WorkManager
            try {
                offlineQueueDao.insertQueuedReport(
                    QueuedReportEntity(
                        childId = null,
                        category = category.ifBlank { "other" },
                        details = content,
                        platform = platform.ifBlank { null },
                        isAnonymous = isAnonymous
                    )
                )
                OfflineSyncWorker.enqueueSync(getApplication())
                _uiState.value = ReportUiState(
                    isSuccess = true,
                    protectedCaseId = "QUEUED-OFFLINE",
                    message = "Saved securely offline. Your report will be automatically transmitted the moment your device reconnects."
                )
            } catch (e: Exception) {
                _uiState.value = ReportUiState(
                    error = "Failed to store offline report: ${e.localizedMessage}"
                )
            }
        }
    }

    fun resetState() {
        _uiState.value = ReportUiState()
    }
}
