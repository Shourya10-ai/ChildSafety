package com.childsafety.app.ui.child

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.data.local.db.OfflineQueueDao
import com.childsafety.app.data.local.db.QueuedReportEntity
import com.childsafety.app.network.CopilotApi
import com.childsafety.app.network.ReportApi
import com.childsafety.app.network.models.CreateReportRequest
import com.childsafety.app.worker.OfflineSyncWorker
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
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
    private val copilotApi: CopilotApi,
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

    fun submitVoiceReport(
        voiceStatement: String,
        platform: String = "Other",
        category: String = "other"
    ) {
        if (voiceStatement.isBlank()) {
            _uiState.value = ReportUiState(error = "Audio statement is empty.")
            return
        }

        viewModelScope.launch {
            _uiState.value = ReportUiState(isLoading = true)
            try {
                val mediaType = "audio/wav".toMediaTypeOrNull()
                val body = voiceStatement.toByteArray(Charsets.UTF_8).toRequestBody(mediaType)
                val filePart = MultipartBody.Part.createFormData("file", "voice_memo.wav", body)
                val platformBody = platform.toRequestBody("text/plain".toMediaTypeOrNull())
                val categoryBody = category.toRequestBody("text/plain".toMediaTypeOrNull())

                val response = copilotApi.submitVoiceReport(filePart, platformBody, categoryBody)
                if (response.isSuccessful && response.body() != null) {
                    val res = response.body()!!
                    _uiState.value = ReportUiState(
                        isSuccess = true,
                        protectedCaseId = res.protectedCaseId,
                        message = "Voice report filed! Transcript: \"${res.transcript}\""
                    )
                    return@launch
                }
            } catch (_: Exception) {}

            // Fallback to text submission
            submitReport(category, platform, voiceStatement, isAnonymous = true)
        }
    }

    fun resetState() {
        _uiState.value = ReportUiState()
    }
}
