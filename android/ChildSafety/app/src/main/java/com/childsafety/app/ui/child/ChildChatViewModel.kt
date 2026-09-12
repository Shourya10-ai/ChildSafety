package com.childsafety.app.ui.child

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.network.ChatApi
import com.childsafety.app.network.CopilotApi
import com.childsafety.app.network.models.ChildSafetyChatRequest
import com.childsafety.app.network.models.ChatMessageRequest
import com.childsafety.app.network.models.ChatMessageResponse
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import java.util.UUID
import javax.inject.Inject

data class ChatUiState(
    val isLoading: Boolean = false,
    val isSending: Boolean = false,
    val error: String? = null,
    val assignedProtector: String? = null,
    val protectedCaseId: String? = null
)

@HiltViewModel
class ChildChatViewModel @Inject constructor(
    private val chatApi: ChatApi,
    private val copilotApi: CopilotApi
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState

    private val _messages = MutableStateFlow<List<ChatMessageResponse>>(emptyList())
    val messages: StateFlow<List<ChatMessageResponse>> = _messages

    private val _isAiMode = MutableStateFlow(false)
    val isAiMode: StateFlow<Boolean> = _isAiMode

    val messageInput = MutableStateFlow("")

    fun setAiMode(enabled: Boolean) {
        _isAiMode.value = enabled
    }

    init {
        loadActiveChat()
    }

    fun loadActiveChat() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)
            try {
                val res = chatApi.getMyActiveChat()
                if (res.isSuccessful && res.body() != null) {
                    val body = res.body()!!
                    _messages.value = body.messages
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        assignedProtector = body.assignedModeratorName ?: "Assigned Child Protector",
                        protectedCaseId = body.protectedCaseId
                    )
                } else {
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        error = "Could not load messages. Server response: ${res.code()}"
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = e.localizedMessage ?: "Network connection error"
                )
            }
        }
    }

    fun sendMessage(customText: String? = null) {
        val textToSend = customText ?: messageInput.value.trim()
        if (textToSend.isBlank()) return

        if (customText == null) {
            messageInput.value = ""
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSending = true)

            if (_isAiMode.value) {
                // 1. AI Safety Guardian Mode
                val userMsg = ChatMessageResponse(
                    id = UUID.randomUUID().toString(),
                    caseId = _uiState.value.protectedCaseId ?: "AI_SESSION",
                    senderId = "me",
                    senderRole = "child",
                    senderName = "Me",
                    content = textToSend,
                    createdAt = "Just now"
                )
                _messages.value = _messages.value + userMsg

                try {
                    val aiReq = ChildSafetyChatRequest(message = textToSend)
                    val aiRes = copilotApi.chatWithSafetyGuardian(aiReq)
                    if (aiRes.isSuccessful && aiRes.body() != null) {
                        val replyBody = aiRes.body()!!
                        val aiMsg = ChatMessageResponse(
                            id = UUID.randomUUID().toString(),
                            caseId = _uiState.value.protectedCaseId ?: "AI_SESSION",
                            senderId = "ai_guardian",
                            senderRole = "assistant",
                            senderName = "🤖 AI Safety Guardian",
                            content = replyBody.reply,
                            createdAt = "Just now"
                        )
                        _messages.value = _messages.value + aiMsg
                    }
                } catch (e: Exception) {
                    val fallbackMsg = ChatMessageResponse(
                        id = UUID.randomUUID().toString(),
                        caseId = "AI_SESSION",
                        senderId = "ai_guardian",
                        senderRole = "assistant",
                        senderName = "🤖 AI Safety Guardian",
                        content = "I am with you. If you ever feel unsafe, you did nothing wrong. Tap SOS above or switch to your live Human Safety Protector anytime.",
                        createdAt = "Just now"
                    )
                    _messages.value = _messages.value + fallbackMsg
                } finally {
                    _uiState.value = _uiState.value.copy(isSending = false)
                }
            } else {
                // 2. Live Human Safety Protector Mode
                try {
                    val req = ChatMessageRequest(content = textToSend)
                    val res = chatApi.sendMessageToMyCase(req)
                    if (res.isSuccessful && res.body() != null) {
                        val sentMsg = res.body()!!
                        _messages.value = _messages.value + sentMsg
                        _uiState.value = _uiState.value.copy(isSending = false)
                    } else {
                        _uiState.value = _uiState.value.copy(
                            isSending = false,
                            error = "Failed to deliver message: ${res.code()}"
                        )
                    }
                } catch (e: Exception) {
                    _uiState.value = _uiState.value.copy(
                        isSending = false,
                        error = e.localizedMessage ?: "Failed to send message"
                    )
                }
            }
        }
    }
}
