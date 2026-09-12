package com.childsafety.app.ui.adult

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MissingChildReportScreen(
    onNavigateBack: () -> Unit,
    viewModel: MissingChildReportViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()

    var childName by remember { mutableStateOf("") }
    var ageText by remember { mutableStateOf("") }
    var gender by remember { mutableStateOf("Male") }
    var heightText by remember { mutableStateOf("") }
    var photoUrl by remember { mutableStateOf("") }
    var lastKnownAddress by remember { mutableStateOf("") }
    var stateName by remember { mutableStateOf("") }
    var districtName by remember { mutableStateOf("") }
    var clothing by remember { mutableStateOf("") }
    var marks by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Report Missing Child", fontWeight = FontWeight.Bold) },
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
            verticalArrangement = Arrangement.spacedBy(14.dp)
        ) {
            if (state.successResult != null) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFE8F5E9))
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Filled.CheckCircle, contentDescription = null, tint = Color(0xFF2E7D32))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                "CRITICAL ALERT BROADCASTED",
                                fontWeight = FontWeight.Black,
                                color = Color(0xFF1B5E20)
                            )
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            "Emergency case filed for ${state.successResult!!.childName}. Local jurisdiction moderators and police dispatchers have been alerted.",
                            color = Color(0xFF1B5E20),
                            style = MaterialTheme.typography.bodyMedium
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Button(
                            onClick = {
                                viewModel.resetState()
                                onNavigateBack()
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2E7D32))
                        ) {
                            Text("Return to Dashboard")
                        }
                    }
                }
            } else {
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Filled.Warning, contentDescription = null, tint = MaterialTheme.colorScheme.error)
                        Spacer(modifier = Modifier.width(10.dp))
                        Text(
                            "Filing a report initiates immediate cross-jurisdiction alerts and triggers Childline & Police tracking.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onErrorContainer
                        )
                    }
                }

                if (state.errorMessage != null) {
                    Text(
                        text = state.errorMessage!!,
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodySmall
                    )
                }

                OutlinedTextField(
                    value = childName,
                    onValueChange = { childName = it },
                    label = { Text("Child's Full Name *") },
                    modifier = Modifier.fillMaxWidth()
                )

                Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = ageText,
                        onValueChange = { ageText = it },
                        label = { Text("Age (Years) *") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f)
                    )
                    OutlinedTextField(
                        value = gender,
                        onValueChange = { gender = it },
                        label = { Text("Gender (M/F/Other)") },
                        modifier = Modifier.weight(1f)
                    )
                }

                Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = heightText,
                        onValueChange = { heightText = it },
                        label = { Text("Height (cm)") },
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.weight(1f)
                    )
                    OutlinedTextField(
                        value = photoUrl,
                        onValueChange = { photoUrl = it },
                        label = { Text("Photo Link") },
                        placeholder = { Text("https://...") },
                        modifier = Modifier.weight(1f)
                    )
                }

                OutlinedTextField(
                    value = lastKnownAddress,
                    onValueChange = { lastKnownAddress = it },
                    label = { Text("Last Known Location / Address *") },
                    modifier = Modifier.fillMaxWidth()
                )

                Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = stateName,
                        onValueChange = { stateName = it },
                        label = { Text("State *") },
                        placeholder = { Text("e.g. Delhi") },
                        modifier = Modifier.weight(1f)
                    )
                    OutlinedTextField(
                        value = districtName,
                        onValueChange = { districtName = it },
                        label = { Text("District *") },
                        placeholder = { Text("e.g. New Delhi") },
                        modifier = Modifier.weight(1f)
                    )
                }

                OutlinedTextField(
                    value = clothing,
                    onValueChange = { clothing = it },
                    label = { Text("Clothing Description") },
                    placeholder = { Text("e.g. Red school shirt, blue trousers") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = marks,
                    onValueChange = { marks = it },
                    label = { Text("Identifying Marks / Scars / Features") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("Circumstances of Disappearance *") },
                    minLines = 3,
                    modifier = Modifier.fillMaxWidth()
                )

                Button(
                    onClick = {
                        val age = ageText.toIntOrNull()
                        val height = heightText.toDoubleOrNull()
                        viewModel.reportMissingChild(
                            childName = childName,
                            photoUrl = photoUrl,
                            description = description,
                            age = age,
                            gender = gender,
                            heightCm = height,
                            clothing = clothing,
                            identifyingMarks = marks,
                            lastKnownAddress = lastKnownAddress,
                            state = stateName,
                            district = districtName
                        )
                    },
                    modifier = Modifier.fillMaxWidth().height(50.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error),
                    enabled = childName.isNotBlank() && lastKnownAddress.isNotBlank() && description.isNotBlank() && !state.isSubmitting
                ) {
                    if (state.isSubmitting) {
                        CircularProgressIndicator(modifier = Modifier.size(20.dp), color = Color.White)
                    } else {
                        Text("Broadcast Emergency Missing Report", fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}
