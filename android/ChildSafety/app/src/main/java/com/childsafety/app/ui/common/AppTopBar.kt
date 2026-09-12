package com.childsafety.app.ui.common

import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.width
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

import androidx.compose.material.icons.filled.Close

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppTopBar(
    title: String,
    mode: String? = null,
    onBackClick: (() -> Unit)? = null,
    onSettingsClick: (() -> Unit)? = null,
    onQuickExitClick: (() -> Unit)? = null
) {
    TopAppBar(
        title = {
            Row {
                Text(text = title)
                if (mode != null) {
                    Spacer(modifier = Modifier.width(8.dp))
                    Badge(containerColor = MaterialTheme.colorScheme.tertiaryContainer) {
                        Text(text = mode, color = MaterialTheme.colorScheme.onTertiaryContainer)
                    }
                }
            }
        },
        navigationIcon = {
            if (onBackClick != null) {
                IconButton(onClick = onBackClick) {
                    Icon(imageVector = Icons.Default.ArrowBack, contentDescription = "Back")
                }
            }
        },
        actions = {
            if (onSettingsClick != null) {
                IconButton(onClick = onSettingsClick) {
                    Icon(imageVector = Icons.Filled.Settings, contentDescription = "Settings")
                }
            }
            if (onQuickExitClick != null) {
                IconButton(onClick = onQuickExitClick) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Quick Stealth Decoy Exit",
                        tint = MaterialTheme.colorScheme.error
                    )
                }
            }
        },
        colors = TopAppBarDefaults.topAppBarColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer,
            titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
        )
    )
}
