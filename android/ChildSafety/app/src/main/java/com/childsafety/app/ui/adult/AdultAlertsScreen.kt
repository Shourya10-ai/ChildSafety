package com.childsafety.app.ui.adult

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

data class Alert(val severity: String, val message: String, val timestamp: String)

@Composable
fun AdultAlertsScreen(
    viewModel: AdultAlertsViewModel = hiltViewModel()
) {
    val alerts by viewModel.alerts.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val context = androidx.compose.ui.platform.LocalContext.current

    var selectedFilter by remember { mutableStateOf("All") }
    val filters = listOf("All", "Critical", "High", "Medium")

    Column(modifier = Modifier.fillMaxSize()) {
        ScrollableTabRow(selectedTabIndex = filters.indexOf(selectedFilter)) {
            filters.forEachIndexed { index, filter ->
                Tab(
                    selected = selectedFilter == filter,
                    onClick = { selectedFilter = filter },
                    text = { Text(filter) }
                )
            }
        }

        if (isLoading && alerts.isEmpty()) {
            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else {
            val filteredAlerts = if (selectedFilter == "All") alerts else alerts.filter { it.severity.equals(selectedFilter, ignoreCase = true) }

            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(filteredAlerts) { alert ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = when (alert.severity.lowercase()) {
                                "critical" -> MaterialTheme.colorScheme.errorContainer
                                "high" -> MaterialTheme.colorScheme.primaryContainer
                                else -> MaterialTheme.colorScheme.surfaceVariant
                            }
                        )
                    ) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                                Text(
                                    text = alert.severity,
                                    style = MaterialTheme.typography.labelMedium,
                                    color = if (alert.severity.lowercase() == "critical") Color.Red else MaterialTheme.colorScheme.primary
                                )
                                Text(alert.timestamp, style = MaterialTheme.typography.labelSmall)
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(alert.message, style = MaterialTheme.typography.titleMedium)
                            Spacer(modifier = Modifier.height(8.dp))
                            if (alert.severity.lowercase() == "critical") {
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Button(
                                        onClick = {
                                            val dial = android.content.Intent(android.content.Intent.ACTION_DIAL, android.net.Uri.parse("tel:112"))
                                            context.startActivity(dial)
                                        },
                                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                                    ) {
                                        Text("Call 112")
                                    }
                                    OutlinedButton(
                                        onClick = {
                                            val dial = android.content.Intent(android.content.Intent.ACTION_DIAL, android.net.Uri.parse("tel:1098"))
                                            context.startActivity(dial)
                                        }
                                    ) {
                                        Text("Helpline 1098")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
