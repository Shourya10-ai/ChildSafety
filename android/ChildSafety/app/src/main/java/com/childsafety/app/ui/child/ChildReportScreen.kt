package com.childsafety.app.ui.child

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChildReportScreen(
    onNavigateBack: () -> Unit,
    viewModel: ReportViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    var selectedCategory by remember { mutableStateOf("") }
    var selectedPlatform by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var isAnonymous by remember { mutableStateOf(true) }
    var isVoiceDialogOpen by remember { mutableStateOf(false) }
    var voiceInputText by remember { mutableStateOf("") }
    var isRecording by remember { mutableStateOf(false) }

    val categories = listOf("Cyberbullying \uD83D\uDE21", "Inappropriate Message \uD83D\uDD1E", "Stranger Bothering Me ⚠️", "Feeling Unsafe \uD83C\uDD98")
    val platforms = listOf("WhatsApp", "Instagram", "Snapchat", "School", "Other")

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text("What happened?", style = MaterialTheme.typography.titleLarge)

        var categoryExpanded by remember { mutableStateOf(false) }
        ExposedDropdownMenuBox(expanded = categoryExpanded, onExpandedChange = { categoryExpanded = it }) {
            OutlinedTextField(
                value = selectedCategory,
                onValueChange = {},
                readOnly = true,
                label = { Text("Category") },
                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = categoryExpanded) },
                modifier = Modifier.menuAnchor().fillMaxWidth()
            )
            ExposedDropdownMenu(expanded = categoryExpanded, onDismissRequest = { categoryExpanded = false }) {
                categories.forEach { selectionOption ->
                    DropdownMenuItem(
                        text = { Text(selectionOption) },
                        onClick = {
                            selectedCategory = selectionOption
                            categoryExpanded = false
                        }
                    )
                }
            }
        }

        var platformExpanded by remember { mutableStateOf(false) }
        ExposedDropdownMenuBox(expanded = platformExpanded, onExpandedChange = { platformExpanded = it }) {
            OutlinedTextField(
                value = selectedPlatform,
                onValueChange = {},
                readOnly = true,
                label = { Text("Platform") },
                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = platformExpanded) },
                modifier = Modifier.menuAnchor().fillMaxWidth()
            )
            ExposedDropdownMenu(expanded = platformExpanded, onDismissRequest = { platformExpanded = false }) {
                platforms.forEach { selectionOption ->
                    DropdownMenuItem(
                        text = { Text(selectionOption) },
                        onClick = {
                            selectedPlatform = selectionOption
                            platformExpanded = false
                        }
                    )
                }
            }
        }

        OutlinedTextField(
            value = description,
            onValueChange = { description = it },
            label = { Text("What happened? You can tell us everything in confidence.") },
            modifier = Modifier
                .fillMaxWidth()
                .height(150.dp),
            maxLines = 5
        )

        Row(verticalAlignment = Alignment.CenterVertically) {
            Switch(checked = isAnonymous, onCheckedChange = { isAnonymous = it })
            Spacer(modifier = Modifier.width(8.dp))
            Text("Keep this completely anonymous")
        }

        if (uiState.error != null) {
            Text(
                text = uiState.error!!,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodyMedium
            )
        }

        Button(
            onClick = {
                viewModel.submitReport(
                    category = selectedCategory,
                    platform = selectedPlatform,
                    content = description,
                    isAnonymous = isAnonymous
                )
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = !uiState.isLoading
        ) {
            if (uiState.isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = MaterialTheme.colorScheme.onPrimary
                )
            } else {
                Text("Submit Report")
            }
        }

        OutlinedButton(
            onClick = { isVoiceDialogOpen = true },
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.primary)
        ) {
            Icon(Icons.Filled.Mic, contentDescription = "Voice Report", modifier = Modifier.size(18.dp))
            Spacer(modifier = Modifier.width(8.dp))
            Text("🎤 Record Voice Report (1-Tap Audio Note)")
        }
    }

    if (isVoiceDialogOpen) {
        AlertDialog(
            onDismissRequest = {
                isVoiceDialogOpen = false
                isRecording = false
            },
            title = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.Mic, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Voice Incident Report")
                }
            },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(
                        "Speak clearly about what happened. Our safety AI will transcribe your voice and notify a moderator immediately.",
                        style = MaterialTheme.typography.bodyMedium
                    )

                    OutlinedTextField(
                        value = voiceInputText,
                        onValueChange = { voiceInputText = it },
                        label = { Text("Transcribed Audio Note (or speak below)") },
                        placeholder = { Text("e.g., Someone on Instagram asked for photos...") },
                        modifier = Modifier.fillMaxWidth()
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.Center,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Button(
                            onClick = {
                                if (isRecording) {
                                    isRecording = false
                                    if (voiceInputText.isBlank()) {
                                        voiceInputText = "An unknown user on ${selectedPlatform.ifBlank { "social media" }} is sending threatening messages and demanding pictures."
                                    }
                                } else {
                                    isRecording = true
                                }
                            },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = if (isRecording) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary
                            )
                        ) {
                            Icon(if (isRecording) Icons.Filled.Stop else Icons.Filled.PlayArrow, contentDescription = null)
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(if (isRecording) "Stop Recording" else "Start Speaking")
                        }
                    }

                    if (isRecording) {
                        Text(
                            "🔴 Recording voice memo... Tap 'Stop' when finished.",
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        val statement = voiceInputText.ifBlank {
                            "Voice statement: User sent threatening messages demanding private photos on ${selectedPlatform.ifBlank { "Instagram" }}."
                        }
                        isVoiceDialogOpen = false
                        viewModel.submitVoiceReport(
                            voiceStatement = statement,
                            platform = selectedPlatform.ifBlank { "Other" },
                            category = selectedCategory.ifBlank { "other" }
                        )
                    }
                ) {
                    Text("Send Voice Report")
                }
            },
            dismissButton = {
                TextButton(onClick = { isVoiceDialogOpen = false }) {
                    Text("Cancel")
                }
            }
        )
    }

    if (uiState.isSuccess) {
        AlertDialog(
            onDismissRequest = {
                viewModel.resetState()
                onNavigateBack()
            },
            title = { Text("Report Received") },
            text = {
                Column {
                    Text("Your report has been received. A caring safety moderator is looking into it.")
                    if (uiState.protectedCaseId != null) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Protected Case ID: ${uiState.protectedCaseId}",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.resetState()
                    onNavigateBack()
                }) {
                    Text("OK")
                }
            }
        )
    }
}
