package com.childsafety.app.ui.child

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.MailOutline
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay

@Composable
fun ChildHomeScreen(
    onNavigateToReport: () -> Unit,
    onNavigateToChat: () -> Unit,
    onNavigateToTips: () -> Unit,
    onSwitchMode: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Shield Protection Banner
        Surface(
            color = MaterialTheme.colorScheme.secondaryContainer,
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(
                text = "🛡️ You are safe & protected",
                modifier = Modifier.padding(16.dp),
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSecondaryContainer,
                style = MaterialTheme.typography.titleMedium
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Protected Child ID Card
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Your Secret ID", style = MaterialTheme.typography.labelLarge)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("C8A3K2PQ", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.weight(1f))
                    Button(onClick = { /* Copy to clipboard */ }) {
                        Text("Copy")
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        // SOS Button
        var isSosActive by remember { mutableStateOf(false) }
        var countdown by remember { mutableStateOf(3) }
        
        LaunchedEffect(isSosActive) {
            if (isSosActive) {
                while (countdown > 0) {
                    delay(1000)
                    countdown--
                }
                // Trigger SOS action
                isSosActive = false
                countdown = 3
            }
        }

        Box(
            modifier = Modifier
                .size(150.dp)
                .clip(CircleShape)
                .background(if (isSosActive) Color.Yellow else MaterialTheme.colorScheme.error)
                .clickable { isSosActive = !isSosActive },
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = if (isSosActive) "$countdown" else "SOS",
                color = if (isSosActive) Color.Black else MaterialTheme.colorScheme.onError,
                fontSize = 40.sp,
                fontWeight = FontWeight.ExtraBold
            )
        }

        Spacer(modifier = Modifier.height(32.dp))

        // Quick Action Cards
        Row(horizontalArrangement = Arrangement.spacedBy(16.dp), modifier = Modifier.fillMaxWidth()) {
            ActionCard(title = "Report a\nProblem", icon = Icons.Filled.Warning, onClick = onNavigateToReport, modifier = Modifier.weight(1f))
            ActionCard(title = "Safety\nChat", icon = Icons.Filled.MailOutline, onClick = onNavigateToChat, modifier = Modifier.weight(1f))
            ActionCard(title = "Safety\nTips", icon = Icons.Filled.Info, onClick = onNavigateToTips, modifier = Modifier.weight(1f))
        }

        Spacer(modifier = Modifier.weight(1f))

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
            Text(title, style = MaterialTheme.typography.bodySmall, textAlign = androidx.compose.ui.text.style.TextAlign.Center)
        }
    }
}
