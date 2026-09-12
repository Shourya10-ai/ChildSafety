package com.childsafety.app.ui.child

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DpdpRightsScreen(
    onNavigateBack: () -> Unit,
    viewModel: DpdpRightsViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()
    var showErasureDialog by remember { mutableStateOf(false) }
    var erasureReason by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("DPDP Privacy & Rights", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Legal Banner
            Card(
                shape = RoundedCornerShape(12.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        Icons.Filled.Lock,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(36.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Column {
                        Text(
                            "Digital Personal Data Protection Act 2023",
                            fontWeight = FontWeight.Bold,
                            style = MaterialTheme.typography.titleSmall
                        )
                        Text(
                            "Section 9 (Children's Data) & Section 12 (Right to Correction & Erasure)",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onPrimaryContainer
                        )
                    }
                }
            }

            if (state.isLoading) {
                Box(modifier = Modifier.fillMaxWidth().height(200.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator()
                }
            } else if (state.rights != null) {
                val r = state.rights!!

                // Status Card
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text("Your Data Custody Status", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium)

                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("Account Role", color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(r.role.uppercase(), fontWeight = FontWeight.SemiBold)
                        }

                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("18+ Adult Self-Custody", color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(
                                if (r.isAdultSelfCustody) "✅ Granted (18+ Complete Privacy)" else "🔒 Supervised (Under 18)",
                                fontWeight = FontWeight.Bold,
                                color = if (r.isAdultSelfCustody) Color(0xFF2E7D32) else MaterialTheme.colorScheme.primary
                            )
                        }

                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("Parental Consent Link", color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(
                                r.consentStatus ?: (if (r.activeConsentOnFile) "Active" else "None / Severed"),
                                fontWeight = FontWeight.SemiBold
                            )
                        }

                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text("Statutory Forensic Lock", color = MaterialTheme.colorScheme.onSurfaceVariant)
                            Text(
                                if (r.forensicRetentionLocked) "🔒 Locked (Active Safety Case)" else "None (Erasure Permitted)",
                                fontWeight = FontWeight.Bold,
                                color = if (r.forensicRetentionLocked) MaterialTheme.colorScheme.error else Color(0xFF2E7D32)
                            )
                        }
                    }
                }

                // Statutory Rights List
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Enforceable Statutory Rights", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleMedium)
                        Spacer(modifier = Modifier.height(8.dp))
                        r.dpdpStatutoryRights.forEach { rightText ->
                            Row(modifier = Modifier.padding(vertical = 4.dp)) {
                                Text("• ", fontWeight = FontWeight.Black, color = MaterialTheme.colorScheme.primary)
                                Text(rightText, style = MaterialTheme.typography.bodySmall)
                            }
                        }
                    }
                }

                // Erasure Result Notice
                if (state.erasureResult != null) {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F5E9)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Filled.CheckCircle, contentDescription = null, tint = Color(0xFF2E7D32))
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("Erasure Request Filed: ${state.erasureResult!!.requestId}", fontWeight = FontWeight.Bold, color = Color(0xFF1B5E20))
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(state.erasureResult!!.notes, style = MaterialTheme.typography.bodySmall, color = Color(0xFF1B5E20))
                        }
                    }
                }

                // Request Erasure Button
                OutlinedButton(
                    onClick = { showErasureDialog = true },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error)
                ) {
                    Icon(Icons.Filled.Delete, contentDescription = null, modifier = Modifier.size(18.dp))
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Exercise Right to Erasure (Section 12)")
                }
            }

            // Erasure Dialog
            if (showErasureDialog) {
                AlertDialog(
                    onDismissRequest = { showErasureDialog = false },
                    title = { Text("Request Data Erasure", fontWeight = FontWeight.Bold) },
                    text = {
                        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            Text(
                                "Under Section 12(2) DPDP Act 2023, you have the right to request deletion of non-essential personal logs. Note: Child protection evidence under Section 63 BSA 2023 / POCSO Act 2012 is legally preserved until moderator clearance.",
                                style = MaterialTheme.typography.bodySmall
                            )
                            OutlinedTextField(
                                value = erasureReason,
                                onValueChange = { erasureReason = it },
                                label = { Text("Reason for Deletion Request") },
                                placeholder = { Text("e.g. Closing account / revoking surveillance") },
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    },
                    confirmButton = {
                        Button(
                            onClick = {
                                if (erasureReason.isNotBlank()) {
                                    viewModel.requestErasure(erasureReason)
                                    showErasureDialog = false
                                }
                            },
                            enabled = erasureReason.isNotBlank() && !state.isSubmittingErasure
                        ) {
                            Text("Submit to Moderator Gate")
                        }
                    },
                    dismissButton = {
                        TextButton(onClick = { showErasureDialog = false }) {
                            Text("Cancel")
                        }
                    }
                )
            }
        }
    }
}
