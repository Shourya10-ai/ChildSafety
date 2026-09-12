package com.childsafety.app.ui.adult

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LinkChildScreen(
    onNavigateBack: () -> Unit,
    viewModel: LinkChildViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    var childId by remember { mutableStateOf("") }
    var selectedRelationship by remember { mutableStateOf("") }
    var showConsentDialog by remember { mutableStateOf(false) }

    val relationships = listOf("Mother", "Father", "Guardian", "Teacher")

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text("Link a Child Profile", style = MaterialTheme.typography.titleLarge)
        
        OutlinedTextField(
            value = childId,
            onValueChange = { childId = it },
            label = { Text("Protected Child ID (e.g. C8A3K2PQ)") },
            modifier = Modifier.fillMaxWidth()
        )

        var expanded by remember { mutableStateOf(false) }
        ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
            OutlinedTextField(
                value = selectedRelationship,
                onValueChange = {},
                readOnly = true,
                label = { Text("Relationship") },
                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                modifier = Modifier.menuAnchor().fillMaxWidth()
            )
            ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                relationships.forEach { selectionOption ->
                    DropdownMenuItem(
                        text = { Text(selectionOption) },
                        onClick = {
                            selectedRelationship = selectionOption
                            expanded = false
                        }
                    )
                }
            }
        }

        Spacer(modifier = Modifier.weight(1f))

        if (uiState is LinkChildState.Loading) {
            CircularProgressIndicator()
        }

        if (uiState is LinkChildState.Error) {
            Text("Error: ${(uiState as LinkChildState.Error).message}", color = MaterialTheme.colorScheme.error)
        }

        Button(
            onClick = {
                if (childId.isNotBlank() && selectedRelationship.isNotBlank()) {
                    showConsentDialog = true
                }
            },
            enabled = childId.isNotBlank() && selectedRelationship.isNotBlank() && uiState !is LinkChildState.Loading,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Link Child")
        }
    }

    if (showConsentDialog) {
        ParentalConsentDialog(
            onConsentGranted = {
                showConsentDialog = false
                viewModel.linkChild(childId, selectedRelationship)
            },
            onDismiss = {
                showConsentDialog = false
            }
        )
    }

    if (uiState is LinkChildState.Success) {
        AlertDialog(
            onDismissRequest = {
                onNavigateBack()
            },
            title = { Text("Child Linked Successfully") },
            text = { Text("DPDP verifiable consent logged. You will now receive alerts and SOS notifications for this child. Child ID: ${(uiState as LinkChildState.Success).childId}. Private counseling chats remain confidential for the child's psychological safety.") },
            confirmButton = {
                TextButton(onClick = {
                    onNavigateBack()
                }) {
                    Text("OK")
                }
            }
        )
    }
}
