package com.childsafety.app.ui.shared

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.platform.LocalContext
import com.childsafety.app.data.local.datastore.AppPreferences

@Composable
fun SessionLockDialog(
    onUnlock: () -> Unit,
    onDismiss: () -> Unit
) {
    var pin by remember { mutableStateOf("") }
    var error by remember { mutableStateOf(false) }
    
    val context = LocalContext.current
    val appPreferences = remember { AppPreferences(context) }
    val storedPin by appPreferences.childPin.collectAsState(initial = null)

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Enter PIN to Exit Child Mode") },
        text = {
            Column {
                Text("Please enter your 4-digit PIN to access Adult mode.")
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = pin,
                    onValueChange = {
                        if (it.length <= 4) {
                            pin = it
                            error = false
                        }
                    },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                    visualTransformation = PasswordVisualTransformation(),
                    isError = error,
                    singleLine = true
                )
                if (error) {
                    Text("Incorrect PIN", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                val validPin = storedPin ?: "1234"
                if (pin == validPin) {
                    onUnlock()
                } else {
                    error = true
                }
            }) {
                Text("Unlock")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancel") }
        }
    )
}
