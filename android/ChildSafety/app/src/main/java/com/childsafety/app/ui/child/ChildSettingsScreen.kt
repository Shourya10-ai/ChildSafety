package com.childsafety.app.ui.child

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChildSettingsScreen(
    onExitChildMode: () -> Unit
) {
    var selectedLanguage by remember { mutableStateOf("English") }
    val languages = listOf("English", "Hindi")
    var showNominateDialog by remember { mutableStateOf(false) }
    var nomineeIdentifier by remember { mutableStateOf("") }
    var nomineeRelationship by remember { mutableStateOf("") }
    var nomineeReason by remember { mutableStateOf("") }
    var nominationSubmittedMessage by remember { mutableStateOf<String?>(null) }

    val scrollState = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text("Settings & Safety Protectors", style = MaterialTheme.typography.titleLarge)

        var languageExpanded by remember { mutableStateOf(false) }
        ExposedDropdownMenuBox(expanded = languageExpanded, onExpandedChange = { languageExpanded = it }) {
            OutlinedTextField(
                value = selectedLanguage,
                onValueChange = {},
                readOnly = true,
                label = { Text("Language") },
                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = languageExpanded) },
                modifier = Modifier.menuAnchor().fillMaxWidth()
            )
            ExposedDropdownMenu(expanded = languageExpanded, onDismissRequest = { languageExpanded = false }) {
                languages.forEach { selectionOption ->
                    DropdownMenuItem(
                        text = { Text(selectionOption) },
                        onClick = {
                            selectedLanguage = selectionOption
                            languageExpanded = false
                        }
                    )
                }
            }
        }

        // Default household guardians
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Default Household Guardians", style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(6.dp))
                Text("• Mom (Primary Guardian)", style = MaterialTheme.typography.bodyMedium)
                Text("• Dad (Primary Guardian)", style = MaterialTheme.typography.bodyMedium)
            }
        }

        // Trusted-Adult Nomination Section
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    "🛡️ Nominated Trusted Adults",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSecondaryContainer
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "If you ever feel unsafe at home, you can nominate an outside trusted adult (like an aunt, teacher, or counselor). Emergency duress alerts can be routed strictly to them, bypassing household guardians.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSecondaryContainer
                )
                Spacer(modifier = Modifier.height(12.dp))

                if (nominationSubmittedMessage != null) {
                    Text(
                        nominationSubmittedMessage!!,
                        style = MaterialTheme.typography.bodySmall,
                        color = Color(0xFF1B5E20)
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                }

                Button(
                    onClick = { showNominateDialog = true },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("+ Nominate Outside Trusted Adult")
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Stealth / Decoy Quick Exit
        OutlinedButton(
            onClick = onExitChildMode,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.primary)
        ) {
            Text("⚡ Quick Stealth Decoy Exit")
        }

        Button(
            onClick = onExitChildMode,
            modifier = Modifier.fillMaxWidth(),
            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
        ) {
            Text("Exit Child Mode")
        }
    }

    if (showNominateDialog) {
        AlertDialog(
            onDismissRequest = { showNominateDialog = false },
            title = { Text("Nominate Trusted Adult") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(
                        "Enter the email or phone of an adult you trust completely. A child safety moderator will vet their profile to protect you.",
                        style = MaterialTheme.typography.bodySmall
                    )
                    OutlinedTextField(
                        value = nomineeIdentifier,
                        onValueChange = { nomineeIdentifier = it },
                        label = { Text("Email or Phone Number") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = nomineeRelationship,
                        onValueChange = { nomineeRelationship = it },
                        label = { Text("Relationship (e.g. Aunt, School Teacher)") },
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = nomineeReason,
                        onValueChange = { nomineeReason = it },
                        label = { Text("Confidential Reason (Optional)") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        if (nomineeIdentifier.isNotBlank() && nomineeRelationship.isNotBlank()) {
                            nominationSubmittedMessage = "✅ Nomination for '${nomineeRelationship}' submitted! Our safety team will vet and approve their access."
                            showNominateDialog = false
                            nomineeIdentifier = ""
                            nomineeRelationship = ""
                            nomineeReason = ""
                        }
                    }
                ) {
                    Text("Submit for Vetting")
                }
            },
            dismissButton = {
                TextButton(onClick = { showNominateDialog = false }) {
                    Text("Cancel")
                }
            }
        )
    }
}
