package com.childsafety.app.ui.shared

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.childsafety.app.ui.adult.AdultHomeScreen
import com.childsafety.app.ui.child.ChildHomeScreen

@Composable
fun SharedHomeScreen(
    onNavigateToReport: () -> Unit,
    onNavigateToChat: () -> Unit,
    onNavigateToTips: () -> Unit,
    onNavigateToLinkChild: () -> Unit,
    onNavigateToAlerts: () -> Unit,
    onNavigateToContacts: () -> Unit,
    onNavigateToSettings: () -> Unit
) {
    var isChildMode by remember { mutableStateOf(false) }
    var showLockDialog by remember { mutableStateOf(false) }

    Column(modifier = Modifier.fillMaxSize()) {
        // Top header embedding SharedProfileSwitcher conceptually
        Surface(
            modifier = Modifier.fillMaxWidth(),
            color = MaterialTheme.colorScheme.primaryContainer
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = androidx.compose.ui.Alignment.CenterVertically
            ) {
                Text(
                    text = if (isChildMode) "Child Profile Active" else "Adult Profile Active",
                    style = MaterialTheme.typography.titleMedium
                )
                Button(onClick = {
                    if (isChildMode) {
                        showLockDialog = true
                    } else {
                        isChildMode = true
                    }
                }) {
                    Text(if (isChildMode) "Exit Child Mode" else "Lock to Child Mode")
                }
            }
        }

        Box(modifier = Modifier.weight(1f)) {
            if (isChildMode) {
                ChildHomeScreen(
                    onNavigateToReport = onNavigateToReport,
                    onNavigateToChat = onNavigateToChat,
                    onNavigateToTips = onNavigateToTips,
                    onSwitchMode = { showLockDialog = true }
                )
            } else {
                AdultHomeScreen(
                    onNavigateToLinkChild = onNavigateToLinkChild,
                    onNavigateToAlerts = onNavigateToAlerts,
                    onNavigateToContacts = onNavigateToContacts,
                    onNavigateToSettings = onNavigateToSettings
                )
            }
        }
    }

    if (showLockDialog) {
        SessionLockDialog(
            onUnlock = {
                isChildMode = false
                showLockDialog = false
            },
            onDismiss = { showLockDialog = false }
        )
    }
}
