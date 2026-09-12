package com.childsafety.app.ui.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.childsafety.app.data.repository.AuthRepository
import com.childsafety.app.data.repository.AuthResult
import com.childsafety.app.network.models.LoginRequest
import com.childsafety.app.network.models.RegisterRequest
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

data class AuthUiState(
    val isLoading: Boolean = false,
    val isSuccess: Boolean = false,
    val error: String? = null,
    val userRole: String? = null,
    val userId: String? = null
)

@HiltViewModel
class AuthViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(AuthUiState())
    val uiState: StateFlow<AuthUiState> = _uiState

    val emailState = MutableStateFlow("")
    val passwordState = MutableStateFlow("")
    val confirmPasswordState = MutableStateFlow("")
    val fullNameState = MutableStateFlow("")
    val selectedRole = MutableStateFlow("child")
    val phoneState = MutableStateFlow("")
    val isPasswordVisible = MutableStateFlow(false)

    // Foundation Hardening: Mandatory Base Info & Setup Paths
    val stateState = MutableStateFlow("Delhi")
    val districtState = MutableStateFlow("Delhi")
    val pinCodeState = MutableStateFlow("")
    val dobState = MutableStateFlow("")
    val childSetupPath = MutableStateFlow("SOLO") // "SOLO" or "COLLABORATIVE"
    val parentEmailState = MutableStateFlow("")
    val schoolNameState = MutableStateFlow("")
    val addressState = MutableStateFlow("")

    fun login() {
        val errorMsg = validateLoginForm()
        if (errorMsg != null) {
            _uiState.value = AuthUiState(error = errorMsg)
            return
        }

        viewModelScope.launch {
            _uiState.value = AuthUiState(isLoading = true)
            when (val result = authRepository.login(LoginRequest(emailState.value, passwordState.value))) {
                is AuthResult.Success -> {
                    _uiState.value = AuthUiState(
                        isSuccess = true,
                        userRole = result.data.role,
                        userId = result.data.userId
                    )
                }
                is AuthResult.Error -> {
                    _uiState.value = AuthUiState(error = result.message)
                }
                else -> Unit
            }
        }
    }

    fun register() {
        val errorMsg = validateRegisterForm()
        if (errorMsg != null) {
            _uiState.value = AuthUiState(error = errorMsg)
            return
        }

        viewModelScope.launch {
            _uiState.value = AuthUiState(isLoading = true)
            val request = RegisterRequest(
                email = emailState.value,
                password = passwordState.value,
                fullName = fullNameState.value,
                role = selectedRole.value,
                phone = phoneState.value.ifBlank { null },
                state = stateState.value.ifBlank { null },
                district = districtState.value.ifBlank { null },
                pinCode = pinCodeState.value.ifBlank { null },
                dateOfBirth = dobState.value.ifBlank { null },
                setupPath = if (selectedRole.value == "child") childSetupPath.value else null,
                schoolName = schoolNameState.value.ifBlank { null },
                linkedViaAdultEmail = if (selectedRole.value == "child" && childSetupPath.value == "COLLABORATIVE") parentEmailState.value.ifBlank { null } else null,
                address = addressState.value.ifBlank { null }
            )
            when (val result = authRepository.register(request)) {
                is AuthResult.Success -> {
                    _uiState.value = AuthUiState(
                        isSuccess = true,
                        userRole = result.data.role,
                        userId = result.data.userId
                    )
                }
                is AuthResult.Error -> {
                    _uiState.value = AuthUiState(error = result.message)
                }
                else -> Unit
            }
        }
    }

    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
            _uiState.value = AuthUiState()
        }
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    fun togglePasswordVisibility() {
        isPasswordVisible.value = !isPasswordVisible.value
    }

    fun isLoggedIn(): Boolean = authRepository.isLoggedIn()

    fun getCurrentRole(): String? = authRepository.getCurrentRole()

    fun validateLoginForm(): String? {
        if (emailState.value.isBlank()) return "Email cannot be empty"
        if (passwordState.value.isBlank()) return "Password cannot be empty"
        return null
    }

    fun validateRegisterForm(): String? {
        if (fullNameState.value.isBlank()) return "Full name cannot be empty"
        if (emailState.value.isBlank()) return "Email cannot be empty"
        if (passwordState.value.isBlank()) return "Password cannot be empty"
        if (passwordState.value.length < 8) return "Password must be at least 8 characters"
        if (!passwordState.value.any { it.isUpperCase() }) return "Password must contain at least one uppercase letter"
        if (!passwordState.value.any { it.isDigit() }) return "Password must contain at least one digit"
        if (passwordState.value != confirmPasswordState.value) return "Passwords do not match"
        if (stateState.value.isBlank()) return "Please enter your state"
        if (districtState.value.isBlank()) return "Please enter your district"
        if (selectedRole.value == "child" && childSetupPath.value == "COLLABORATIVE" && parentEmailState.value.isBlank()) {
            return "Please enter parent/guardian email to link"
        }
        return null
    }
}
