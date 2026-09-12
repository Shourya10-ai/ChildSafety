package com.childsafety.app.ui.adult

import android.content.Intent
import android.net.Uri
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Call
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Place
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun AdultHomeScreen(
    onNavigateToLinkChild: () -> Unit,
    onNavigateToAlerts: () -> Unit,
    onNavigateToContacts: () -> Unit,
    onNavigateToSettings: () -> Unit,
    viewModel: AdultAlertsViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val activeSosList by viewModel.activeSosList.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Critical Active SOS Banner (If child triggered SOS)
        AnimatedVisibility(visible = activeSosList.isNotEmpty()) {
            val emergency = activeSosList.firstOrNull()
            emergency?.let { ev ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                Icons.Filled.Warning,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.error,
                                modifier = Modifier.size(28.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                "🚨 CRITICAL SOS ALERT ACTIVE",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Black,
                                color = MaterialTheme.colorScheme.error
                            )
                        }

                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Child: ${ev.childName ?: ev.protectedChildId ?: "Protected Child"}",
                            fontWeight = FontWeight.Bold,
                            style = MaterialTheme.typography.bodyLarge
                        )
                        Text(
                            text = ev.message ?: "Emergency beacon activated by child.",
                            style = MaterialTheme.typography.bodyMedium
                        )

                        if (ev.latitude != null && ev.longitude != null) {
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "Coordinates: %.5f, %.5f (±%.0fm)".format(ev.latitude, ev.longitude, ev.accuracy ?: 10f),
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }

                        Spacer(modifier = Modifier.height(12.dp))

                        // Action buttons: Maps, Call Police 112, Call Childline 1098, Resolve
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            if (ev.latitude != null && ev.longitude != null) {
                                Button(
                                    onClick = {
                                        val geoUri = Uri.parse("geo:${ev.latitude},${ev.longitude}?q=${ev.latitude},${ev.longitude}(Child+Emergency)")
                                        val mapIntent = Intent(Intent.ACTION_VIEW, geoUri)
                                        mapIntent.setPackage("com.google.android.apps.maps")
                                        try {
                                            context.startActivity(mapIntent)
                                        } catch (_: Exception) {
                                            context.startActivity(Intent(Intent.ACTION_VIEW, geoUri))
                                        }
                                    },
                                    modifier = Modifier.weight(1f),
                                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
                                ) {
                                    Icon(Icons.Filled.Place, contentDescription = null, modifier = Modifier.size(16.dp))
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text("Maps")
                                }
                            }

                            Button(
                                onClick = { viewModel.resolveSos(ev.id) },
                                modifier = Modifier.weight(1f),
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2E7D32))
                            ) {
                                Icon(Icons.Filled.CheckCircle, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text("Resolve")
                            }
                        }

                        Spacer(modifier = Modifier.height(8.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            OutlinedButton(
                                onClick = {
                                    val dial = Intent(Intent.ACTION_DIAL, Uri.parse("tel:112"))
                                    context.startActivity(dial)
                                },
                                modifier = Modifier.weight(1f)
                            ) {
                                Icon(Icons.Filled.Call, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text("112 Police")
                            }
                            OutlinedButton(
                                onClick = {
                                    val dial = Intent(Intent.ACTION_DIAL, Uri.parse("tel:1098"))
                                    context.startActivity(dial)
                                },
                                modifier = Modifier.weight(1f)
                            ) {
                                Icon(Icons.Filled.Call, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text("1098 Childline")
                            }
                        }
                    }
                }
            }
        }

        // Family Safety Status Header
        Text("Family Safety Overview", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)

        // Linked Children List
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Leo (Protected ID: C8A3K2PQ)", fontWeight = FontWeight.Bold)
                Text(
                    text = if (activeSosList.isNotEmpty()) "Status: 🚨 EMERGENCY ACTIVE" else "Status: Active • Safe",
                    color = if (activeSosList.isNotEmpty()) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.SemiBold
                )
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

        // Recent Alerts Card
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onNavigateToAlerts() },
            colors = CardDefaults.cardColors(
                containerColor = if (activeSosList.isNotEmpty()) MaterialTheme.colorScheme.errorContainer else MaterialTheme.colorScheme.surfaceVariant
            )
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = "Alerts & Notifications",
                    style = MaterialTheme.typography.titleMedium,
                    color = if (activeSosList.isNotEmpty()) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = if (activeSosList.isNotEmpty()) "🚨 1 Active Emergency SOS requires immediate review!" else "No critical emergencies. View all safety alerts.",
                    color = if (activeSosList.isNotEmpty()) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }

        Spacer(modifier = Modifier.height(4.dp))
        Text("Quick Access & Helplines", style = MaterialTheme.typography.titleMedium)

        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(16.dp)) {
            Button(onClick = onNavigateToContacts, modifier = Modifier.weight(1f)) {
                Text("Contacts")
            }
            Button(
                onClick = {
                    val dial = Intent(Intent.ACTION_DIAL, Uri.parse("tel:1098"))
                    context.startActivity(dial)
                },
                modifier = Modifier.weight(1f)
            ) {
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
