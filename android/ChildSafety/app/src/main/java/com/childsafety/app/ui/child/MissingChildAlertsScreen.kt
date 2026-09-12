package com.childsafety.app.ui.child

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
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
import com.childsafety.app.network.models.MissingChildResponse

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MissingChildAlertsScreen(
    onNavigateBack: () -> Unit,
    viewModel: MissingChildAlertsViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()
    var selectedChildForSighting by remember { mutableStateOf<MissingChildResponse?>(null) }
    var sightingAddress by remember { mutableStateOf("") }
    var sightingNotes by remember { mutableStateOf("") }
    var sightingPhotoUrl by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Missing Child Alerts", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Filled.ArrowBack, contentDescription = "Back")
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.loadAlerts() }) {
                        Icon(Icons.Filled.Refresh, contentDescription = "Refresh")
                    }
                }
            )
        }
    ) { padding ->
        Box(modifier = Modifier.fillMaxSize().padding(padding)) {
            Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
                // Banner
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
                ) {
                    Row(
                        modifier = Modifier.padding(14.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Filled.Warning,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.error,
                            modifier = Modifier.size(32.dp)
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                "NATIONAL EMERGENCY ALERTS",
                                style = MaterialTheme.typography.titleSmall,
                                fontWeight = FontWeight.Black,
                                color = MaterialTheme.colorScheme.error
                            )
                            Text(
                                "Active missing child notices from Police & Childline. If spotted, report a sighting immediately.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onErrorContainer
                            )
                        }
                    }
                }

                if (state.sightingSuccessMessage != null) {
                    Spacer(modifier = Modifier.height(10.dp))
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F5E9)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(Icons.Filled.CheckCircle, contentDescription = null, tint = Color(0xFF2E7D32))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                state.sightingSuccessMessage!!,
                                color = Color(0xFF1B5E20),
                                style = MaterialTheme.typography.bodySmall,
                                modifier = Modifier.weight(1f)
                            )
                            IconButton(onClick = { viewModel.clearSightingSuccess() }) {
                                Icon(Icons.Filled.Close, contentDescription = "Dismiss", tint = Color(0xFF2E7D32))
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                if (state.isLoading) {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        CircularProgressIndicator()
                    }
                } else if (state.alerts.isEmpty()) {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Icon(
                                Icons.Filled.CheckCircle,
                                contentDescription = null,
                                tint = Color(0xFF4CAF50),
                                modifier = Modifier.size(56.dp)
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                "No active missing child alerts in your region.",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.SemiBold
                            )
                            Text(
                                "Tap refresh to check national safety feeds.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                } else {
                    LazyColumn(
                        verticalArrangement = Arrangement.spacedBy(14.dp),
                        modifier = Modifier.fillMaxSize()
                    ) {
                        items(state.alerts) { child ->
                            MissingChildCard(
                                child = child,
                                onReportSightingClick = {
                                    selectedChildForSighting = child
                                    sightingAddress = ""
                                    sightingNotes = ""
                                    sightingPhotoUrl = ""
                                }
                            )
                        }
                    }
                }
            }

            // Sighting Dialog
            if (selectedChildForSighting != null) {
                AlertDialog(
                    onDismissRequest = { selectedChildForSighting = null },
                    title = {
                        Text("Report Sighting: ${selectedChildForSighting!!.childName}", fontWeight = FontWeight.Bold)
                    },
                    text = {
                        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                            Text(
                                "Provide accurate location details. Your report goes directly to the investigating police officer and assigned safety moderator.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            OutlinedTextField(
                                value = sightingAddress,
                                onValueChange = { sightingAddress = it },
                                label = { Text("Exact Sighting Location / Landmark") },
                                placeholder = { Text("e.g. Near Rajiv Chowk Metro Gate 3") },
                                modifier = Modifier.fillMaxWidth()
                            )
                            OutlinedTextField(
                                value = sightingNotes,
                                onValueChange = { sightingNotes = it },
                                label = { Text("Observation Notes") },
                                placeholder = { Text("e.g. Accompanied by tall man in black jacket") },
                                modifier = Modifier.fillMaxWidth(),
                                minLines = 2
                            )
                            OutlinedTextField(
                                value = sightingPhotoUrl,
                                onValueChange = { sightingPhotoUrl = it },
                                label = { Text("Photo Evidence URL (Optional)") },
                                placeholder = { Text("https://...") },
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    },
                    confirmButton = {
                        Button(
                            onClick = {
                                if (sightingAddress.isNotBlank()) {
                                    viewModel.submitSighting(
                                        missingChildId = selectedChildForSighting!!.id,
                                        locationAddress = sightingAddress,
                                        sightingNotes = sightingNotes,
                                        imageUrl = sightingPhotoUrl.ifBlank { null }
                                    )
                                    selectedChildForSighting = null
                                }
                            },
                            enabled = sightingAddress.isNotBlank() && !state.isSubmittingSighting
                        ) {
                            if (state.isSubmittingSighting) {
                                CircularProgressIndicator(modifier = Modifier.size(16.dp), color = Color.White)
                            } else {
                                Text("Submit Sighting")
                            }
                        }
                    },
                    dismissButton = {
                        TextButton(onClick = { selectedChildForSighting = null }) {
                            Text("Cancel")
                        }
                    }
                )
            }
        }
    }
}

@Composable
fun MissingChildCard(
    child: MissingChildResponse,
    onReportSightingClick: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = child.childName,
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                Surface(
                    color = MaterialTheme.colorScheme.error,
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Text(
                        text = "🔴 ${child.status}",
                        color = Color.White,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            val detailsList = buildList {
                if (child.ageWhenMissing != null) add("Age: ${child.ageWhenMissing} yrs")
                if (!child.gender.isNullOrBlank()) add("Gender: ${child.gender}")
                if (child.heightCm != null) add("Height: ${child.heightCm.toInt()} cm")
            }
            if (detailsList.isNotEmpty()) {
                Text(
                    text = detailsList.joinToString(" • "),
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = MaterialTheme.colorScheme.primary
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            if (!child.lastKnownAddress.isNullOrBlank()) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.Place, contentDescription = null, modifier = Modifier.size(16.dp), tint = MaterialTheme.colorScheme.error)
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = "Last seen: ${child.lastKnownAddress}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            if (!child.clothingDescription.isNullOrBlank()) {
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "Wearing: ${child.clothingDescription}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            if (!child.identifyingMarks.isNullOrBlank()) {
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "Marks: ${child.identifyingMarks}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = child.description,
                style = MaterialTheme.typography.bodySmall
            )

            Spacer(modifier = Modifier.height(12.dp))

            Button(
                onClick = onReportSightingClick,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
            ) {
                Icon(Icons.Filled.Search, contentDescription = null, modifier = Modifier.size(18.dp))
                Spacer(modifier = Modifier.width(8.dp))
                Text("Report a Sighting")
            }
        }
    }
}
