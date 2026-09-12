package com.childsafety.app.ui.child

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
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
