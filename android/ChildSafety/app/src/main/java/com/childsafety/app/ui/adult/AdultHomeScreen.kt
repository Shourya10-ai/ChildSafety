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
import androidx.compose.material.icons.filled.*
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
    onNavigateToReportMissingChild: () -> Unit = {},
    onNavigateToMissingChildAlerts: () -> Unit = {},
    onNavigateToDpdpRights: () -> Unit = {},
    viewModel: AdultAlertsViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val activeSosList by viewModel.activeSosList.collectAsState()
    val linkedChildren by viewModel.linkedChildren.collectAsState()
    val primaryChildRisk by viewModel.primaryChildRisk.collectAsState()
    val graphStats by viewModel.graphStats.collectAsState()

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

        // Linked Children List & Predictive Risk
        if (linkedChildren.isNotEmpty()) {
            linkedChildren.forEach { child ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "${child.displayName} (${child.protectedChildId})",
                                fontWeight = FontWeight.Bold,
                                style = MaterialTheme.typography.titleMedium,
                                modifier = Modifier.weight(1f)
                            )
                            primaryChildRisk?.let { risk ->
                                val tierColor = when (risk.threatTier) {
                                    "CRITICAL" -> Color(0xFFD32F2F)
                                    "HIGH" -> Color(0xFFE65100)
                                    "MEDIUM" -> Color(0xFFF57C00)
                                    else -> Color(0xFF2E7D32)
                                }
                                Surface(
                                    color = tierColor.copy(alpha = 0.15f),
                                    shape = RoundedCornerShape(8.dp)
                                ) {
                                    Text(
                                        text = "${risk.threatTier} RISK",
                                        color = tierColor,
                                        fontWeight = FontWeight.Black,
                                        style = MaterialTheme.typography.labelMedium,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                    )
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = if (activeSosList.isNotEmpty()) "Status: 🚨 EMERGENCY ACTIVE" else "Status: Active • Shield Monitoring",
                            color = if (activeSosList.isNotEmpty()) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary,
                            fontWeight = FontWeight.SemiBold
                        )

                        primaryChildRisk?.let { risk ->
                            Spacer(modifier = Modifier.height(8.dp))
                            LinearProgressIndicator(
                                progress = { risk.compositeRiskScore.toFloat() },
                                modifier = Modifier.fillMaxWidth().height(6.dp),
                                color = when (risk.threatTier) {
                                    "CRITICAL", "HIGH" -> MaterialTheme.colorScheme.error
                                    "MEDIUM" -> Color(0xFFF57C00)
                                    else -> Color(0xFF2E7D32)
                                }
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text(
                                    text = "AI Threat Index: ${(risk.compositeRiskScore * 100).toInt()}%",
                                    style = MaterialTheme.typography.bodySmall,
                                    fontWeight = FontWeight.Bold
                                )
                                Text(
                                    text = "Velocity: ${(risk.factors.velocityScore * 100).toInt()}% | Persistence: ${(risk.factors.predatorPersistenceScore * 100).toInt()}%",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }

                            if (risk.statutoryCitations.isNotEmpty()) {
                                Spacer(modifier = Modifier.height(6.dp))
                                Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                                    risk.statutoryCitations.take(2).forEach { cit ->
                                        Surface(
                                            color = MaterialTheme.colorScheme.secondaryContainer,
                                            shape = RoundedCornerShape(4.dp)
                                        ) {
                                            Text(
                                                text = "${cit.act} ${cit.section}",
                                                style = MaterialTheme.typography.labelSmall,
                                                color = MaterialTheme.colorScheme.onSecondaryContainer,
                                                modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } else {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("No Linked Children Yet", fontWeight = FontWeight.Bold)
                    Text("Link a child using their secret protected ID to enable real-time predictive risk monitoring.", style = MaterialTheme.typography.bodySmall)
                }
            }
        }

        // Global Knowledge Graph Stats Card
        graphStats?.let { stats ->
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.Share, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                    Spacer(modifier = Modifier.width(12.dp))
                    Column {
                        Text(
                            text = "Safety Intelligence Graph: ${stats.totalNodes} Nodes",
                            fontWeight = FontWeight.Bold,
                            style = MaterialTheme.typography.titleSmall
                        )
                        Text(
                            text = "Tracking ${stats.casesCount} cases, ${stats.suspectsCount} suspect handles & ${stats.multiVictimPredatorsCount} multi-victim serial predators across districts.",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
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

        // Phase 9: Missing Child Network & DPDP Act Controls
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onNavigateToReportMissingChild() },
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
        ) {
            Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.Warning, contentDescription = null, tint = MaterialTheme.colorScheme.error)
                Spacer(modifier = Modifier.width(12.dp))
                Column {
                    Text("Report Missing Child (Emergency)", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.titleSmall)
                    Text("Broadcast urgent missing notice to police and moderators", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onErrorContainer)
                }
            }
        }

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onNavigateToMissingChildAlerts() },
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
        ) {
            Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.Place, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                Spacer(modifier = Modifier.width(12.dp))
                Column {
                    Text("Active Missing Child Search Alerts", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleSmall)
                    Text("Review open alerts and sightings in your district", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
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

        OutlinedButton(onClick = onNavigateToDpdpRights, modifier = Modifier.fillMaxWidth()) {
            Icon(Icons.Filled.Lock, contentDescription = "DPDP Rights")
            Spacer(modifier = Modifier.width(8.dp))
            Text("DPDP Act Privacy & Rights Portal")
        }
    }
}
