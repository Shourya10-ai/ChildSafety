package com.childsafety.app.ui.adult

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@Composable
fun AdultHomeScreen(
    onNavigateToLinkChild: () -> Unit,
    onNavigateToAlerts: () -> Unit,
    onNavigateToContacts: () -> Unit,
    onNavigateToSettings: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Family Safety Status Header
        Text("1 Child Protected", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)

        // Linked Children List
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Leo (Protected ID: C8A3K2PQ)", fontWeight = FontWeight.Bold)
                Text("Status: Active • Safe", color = MaterialTheme.colorScheme.primary)
            }
        }

        Button(
            onClick = onNavigateToLinkChild,
            modifier = Modifier.fillMaxWidth()
        ) {
            Icon(Icons.Filled.Add, contentDescription = "Link Child")
            Spacer(modifier = Modifier.width(8.dp))
            Text("Link Child")
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Recent Alerts Card
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onNavigateToAlerts() },
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Recent Alerts", style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.onErrorContainer)
                Text("No critical SOS alerts today.", color = MaterialTheme.colorScheme.onErrorContainer)
            }
        }

        Spacer(modifier = Modifier.height(16.dp))
        Text("Quick Access", style = MaterialTheme.typography.titleMedium)

        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Button(onClick = onNavigateToContacts, modifier = Modifier.weight(1f)) {
                Text("Contacts")
            }
            Button(onClick = { /* Child Helpline */ }, modifier = Modifier.weight(1f)) {
                Text("Helpline 1098")
            }
        }
        Button(onClick = onNavigateToSettings, modifier = Modifier.fillMaxWidth()) {
            Icon(Icons.Filled.Settings, contentDescription = "Settings")
            Spacer(modifier = Modifier.width(8.dp))
            Text("Settings")
        }
    }
}
