package com.childsafety.app.ui.mode

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

@Composable
fun ModeSelectionScreen(
    onModeSelected: (String) -> Unit
) {
    var selectedMode by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(modifier = Modifier.height(32.dp))
        
        Text(
            text = "How will this device be used?",
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = "Choose the mode that fits your situation",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        ModeCard(
            title = "\uD83D\uDC66 Child Mode",
            description = "This is my personal phone",
            details = "Access safety tools, anonymous reporting, SOS",
            isSelected = selectedMode == "CHILD",
            onClick = { selectedMode = "CHILD" }
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        ModeCard(
            title = "\uD83D\uDC68 Adult Mode",
            description = "I am a parent or guardian",
            details = "Manage children, emergency alerts, safety controls",
            isSelected = selectedMode == "ADULT",
            onClick = { selectedMode = "ADULT" }
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        ModeCard(
            title = "\uD83D\uDC68\u200D\uD83D\uDC66 Shared Device Mode",
            description = "We share this family phone",
            details = "Protected child sessions, profile switching, privacy boundaries",
            isSelected = selectedMode == "SHARED",
            onClick = { selectedMode = "SHARED" }
        )
        
        Spacer(modifier = Modifier.weight(1f))
        
        Button(
            onClick = {
                selectedMode?.let { onModeSelected(it) }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = selectedMode != null
        ) {
            Text(text = "Confirm Mode", modifier = Modifier.padding(8.dp))
        }
        
        Spacer(modifier = Modifier.height(32.dp))
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ModeCard(
    title: String,
    description: String,
    details: String,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        onClick = onClick,
        colors = CardDefaults.cardColors(
            containerColor = if (isSelected) MaterialTheme.colorScheme.primaryContainer else MaterialTheme.colorScheme.surfaceVariant
        ),
        border = if (isSelected) BorderStroke(2.dp, MaterialTheme.colorScheme.primary) else null
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = if (isSelected) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = description,
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Medium,
                color = if (isSelected) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = details,
                style = MaterialTheme.typography.bodyMedium,
                color = if (isSelected) MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f) else MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
