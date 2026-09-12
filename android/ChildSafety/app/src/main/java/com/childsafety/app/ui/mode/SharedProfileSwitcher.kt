package com.childsafety.app.ui.mode

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@Composable
fun SharedProfileSwitcher(
    isAdultSession: Boolean,
    onSwitchToChild: () -> Unit,
    onSwitchToAdult: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isAdultSession) MaterialTheme.colorScheme.tertiaryContainer else MaterialTheme.colorScheme.secondaryContainer
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Text(
                    text = "Current Session",
                    style = MaterialTheme.typography.labelMedium,
                    color = if (isAdultSession) MaterialTheme.colorScheme.onTertiaryContainer else MaterialTheme.colorScheme.onSecondaryContainer
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = if (isAdultSession) "\uD83D\uDC68 Adult Profile" else "\uD83D\uDC66 Child Profile",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = if (isAdultSession) MaterialTheme.colorScheme.onTertiaryContainer else MaterialTheme.colorScheme.onSecondaryContainer
                )
            }
            
            Button(
                onClick = {
                    if (isAdultSession) {
                        onSwitchToChild()
                    } else {
                        onSwitchToAdult()
                    }
                },
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isAdultSession) MaterialTheme.colorScheme.tertiary else MaterialTheme.colorScheme.secondary
                )
            ) {
                Text(text = "Switch")
            }
        }
    }
}
