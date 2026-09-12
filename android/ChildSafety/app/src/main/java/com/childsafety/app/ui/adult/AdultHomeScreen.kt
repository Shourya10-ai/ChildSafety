package com.childsafety.app.ui.adult

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun AdultHomeScreen(
    onAddChild: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        Text(text = "Parent Dashboard", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(16.dp))
        
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
        ) {
            Text(
                text = "Emergency Status: All Clear",
                modifier = Modifier.padding(16.dp),
                color = MaterialTheme.colorScheme.onErrorContainer
            )
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Text(text = "Linked Children", style = MaterialTheme.typography.titleLarge)
        Spacer(modifier = Modifier.height(8.dp))
        Text("No children linked yet.", style = MaterialTheme.typography.bodyMedium)
        
        Spacer(modifier = Modifier.weight(1f))
        
        Button(
            onClick = onAddChild,
            modifier = Modifier.align(Alignment.CenterHorizontally)
        ) {
            Text("Add Child")
        }
    }
}
