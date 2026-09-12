package com.childsafety.app.ui.adult

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LinkChildScreen(
    onNavigateBack: () -> Unit
) {
    var childId by remember { mutableStateOf("") }
    var selectedRelationship by remember { mutableStateOf("") }
    var showSuccessDialog by remember { mutableStateOf(false) }

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

        Button(
            onClick = { showSuccessDialog = true },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Link Child")
        }
    }

    if (showSuccessDialog) {
        AlertDialog(
            onDismissRequest = {
                showSuccessDialog = false
                onNavigateBack()
            },
            title = { Text("Child Linked Successfully") },
            text = { Text("You will now receive alerts and SOS notifications for this child. Please note that private counseling chats remain confidential for the child's trust.") },
            confirmButton = {
                TextButton(onClick = {
                    showSuccessDialog = false
                    onNavigateBack()
                }) {
                    Text("OK")
                }
            }
        )
    }
}
