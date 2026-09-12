package com.childsafety.app.ui.child

import android.Manifest
import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel

@Composable
fun ChildHomeScreen(
    onNavigateToReport: () -> Unit,
    onNavigateToChat: () -> Unit,
    onNavigateToTips: () -> Unit,
    onNavigateToMissingAlerts: () -> Unit = {},
    onSwitchMode: () -> Unit,
    viewModel: SosViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val clipboardManager = LocalClipboardManager.current

    val isCountdownActive by viewModel.isCountdownActive.collectAsState()
    val countdownSeconds by viewModel.countdownSeconds.collectAsState()
    val activeSos by viewModel.activeSos.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val statusMsg by viewModel.statusMessage.collectAsState()

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        // Permissions granted or denied, proceed with countdown
        viewModel.startSosCountdown()
    }

    val isEmergency = activeSos != null
    val sosBgColor by animateColorAsState(
        targetValue = when {
            isEmergency -> MaterialTheme.colorScheme.error
            isCountdownActive -> Color(0xFFFFB300) // Amber / Warning
            else -> MaterialTheme.colorScheme.error
        },
        label = "sos_button_color"
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Top Protection / Emergency Banner
        Surface(
            color = if (isEmergency) MaterialTheme.colorScheme.errorContainer else MaterialTheme.colorScheme.secondaryContainer,
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(
                modifier = Modifier.padding(16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = if (isEmergency) "🚨 EMERGENCY ACTIVE • Help is on the way!" else "🛡️ You are safe & protected",
                    fontWeight = FontWeight.Bold,
                    color = if (isEmergency) MaterialTheme.colorScheme.onErrorContainer else MaterialTheme.colorScheme.onSecondaryContainer,
                    style = MaterialTheme.typography.titleMedium
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Protected Child Secret ID Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Your Secret Child ID", style = MaterialTheme.typography.labelLarge)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    val displayId = activeSos?.protectedChildId ?: "C8A3K2PQ"
                    Text(
                        text = displayId,
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.weight(1f))
                    Button(onClick = {
                        clipboardManager.setText(AnnotatedString(displayId))
                    }) {
                        Text("Copy")
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(20.dp))

        // Active Emergency Card (Visible when SOS is triggered)
        AnimatedVisibility(visible = isEmergency) {
            activeSos?.let { event ->
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(bottom = 16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "EMERGENCY BROADCAST ACTIVE",
                            fontWeight = FontWeight.Black,
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.titleMedium
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = "Guardians Notified: ${event.notifiedGuardiansCount} • Case: ${event.protectedCaseId ?: "ACTIVE"}",
                            style = MaterialTheme.typography.bodyMedium,
                            textAlign = TextAlign.Center
                        )
                        if (event.latitude != null && event.longitude != null) {
                            Text(
                                text = "GPS: %.4f, %.4f (±%.0fm)".format(event.latitude, event.longitude, event.accuracy ?: 10f),
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(
                                onClick = { viewModel.resolveSos() },
                                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2E7D32))
                            ) {
                                Icon(Icons.Filled.CheckCircle, contentDescription = null, modifier = Modifier.size(18.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("I Am Safe Now")
                            }
                            OutlinedButton(
                                onClick = {
                                    val dial = Intent(Intent.ACTION_DIAL, Uri.parse("tel:1098"))
                                    context.startActivity(dial)
                                }
                            ) {
                                Icon(Icons.Filled.Call, contentDescription = null, modifier = Modifier.size(18.dp))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text("1098")
                            }
                        }
                    }
                }
            }
        }

        // SOS Button
        Box(
            modifier = Modifier
                .size(160.dp)
                .clip(CircleShape)
                .background(sosBgColor)
                .clickable {
                    if (isEmergency) {
                        // Already active
                    } else if (isCountdownActive) {
                        viewModel.cancelSosCountdown()
                    } else {
                        permissionLauncher.launch(
                            arrayOf(
                                Manifest.permission.ACCESS_FINE_LOCATION,
                                Manifest.permission.ACCESS_COARSE_LOCATION
                            )
                        )
                    }
                },
            contentAlignment = Alignment.Center
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                if (isLoading) {
                    CircularProgressIndicator(color = Color.White)
                } else if (isCountdownActive) {
                    Text(
                        text = "$countdownSeconds",
                        color = Color.Black,
                        fontSize = 48.sp,
                        fontWeight = FontWeight.ExtraBold
                    )
                    Text(
                        text = "TAP TO CANCEL",
                        color = Color.Black,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                } else if (isEmergency) {
                    Text(
                        text = "ACTIVE",
                        color = MaterialTheme.colorScheme.onError,
                        fontSize = 24.sp,
                        fontWeight = FontWeight.Black
                    )
                    Text(
                        text = "HELP COMING",
                        color = MaterialTheme.colorScheme.onError,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                } else {
                    Text(
                        text = "SOS",
                        color = MaterialTheme.colorScheme.onError,
                        fontSize = 44.sp,
                        fontWeight = FontWeight.ExtraBold
                    )
                    Text(
                        text = "3s Hold / Tap",
                        color = MaterialTheme.colorScheme.onError.copy(alpha = 0.8f),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }

        if (statusMsg != null) {
            Spacer(modifier = Modifier.height(10.dp))
            Text(
                text = statusMsg!!,
                style = MaterialTheme.typography.bodySmall,
                color = if (isEmergency) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary,
                textAlign = TextAlign.Center
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Quick Action Cards
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
            ActionCard(title = "Report a\nProblem", icon = Icons.Filled.Warning, onClick = onNavigateToReport, modifier = Modifier.weight(1f))
            ActionCard(title = "Safety\nChat", icon = Icons.Filled.MailOutline, onClick = onNavigateToChat, modifier = Modifier.weight(1f))
            ActionCard(title = "Safety\nTips", icon = Icons.Filled.Info, onClick = onNavigateToTips, modifier = Modifier.weight(1f))
        }

        Spacer(modifier = Modifier.height(14.dp))

        // Missing Child Alerts Card
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { onNavigateToMissingAlerts() },
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
        ) {
            Row(modifier = Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Filled.Search, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                Spacer(modifier = Modifier.width(12.dp))
                Column {
                    Text("Missing Child Alerts & Sightings", fontWeight = FontWeight.Bold, style = MaterialTheme.typography.titleSmall)
                    Text("View active search notices and submit citizen sightings", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Direct Emergency Dial Strip
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
                Text("Police 112")
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
                Text("Child 1098")
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        TextButton(onClick = onSwitchMode) {
            Text("Switch Mode")
        }
    }
}

@Composable
fun ActionCard(title: String, icon: androidx.compose.ui.graphics.vector.ImageVector, onClick: () -> Unit, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier
            .height(100.dp)
            .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(imageVector = icon, contentDescription = title, modifier = Modifier.size(32.dp))
            Spacer(modifier = Modifier.height(4.dp))
            Text(title, style = MaterialTheme.typography.bodySmall, textAlign = TextAlign.Center)
        }
    }
}
