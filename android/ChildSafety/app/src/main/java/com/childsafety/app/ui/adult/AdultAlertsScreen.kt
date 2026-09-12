package com.childsafety.app.ui.adult

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

data class Alert(val severity: String, val message: String, val timestamp: String)

@Composable
fun AdultAlertsScreen() {
    val alerts = listOf(
        Alert("Critical", "SOS Triggered by Leo", "10:32 AM"),
        Alert("High", "Inappropriate Message Blocked", "Yesterday"),
        Alert("Medium", "Device out of safe zone", "Monday")
    )

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

        val filteredAlerts = if (selectedFilter == "All") alerts else alerts.filter { it.severity == selectedFilter }

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
                        containerColor = when (alert.severity) {
                            "Critical" -> MaterialTheme.colorScheme.errorContainer
                            "High" -> MaterialTheme.colorScheme.primaryContainer
                            else -> MaterialTheme.colorScheme.surfaceVariant
                        }
                    )
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                            Text(alert.severity, style = MaterialTheme.typography.labelMedium, color = Color.Red)
                            Text(alert.timestamp, style = MaterialTheme.typography.labelSmall)
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(alert.message, style = MaterialTheme.typography.titleMedium)
                        Spacer(modifier = Modifier.height(8.dp))
                        if (alert.severity == "Critical") {
                            Button(onClick = { /* Emergency Action */ }) {
                                Text("Emergency Action")
                            }
                        }
                    }
                }
            }
        }
    }
}
