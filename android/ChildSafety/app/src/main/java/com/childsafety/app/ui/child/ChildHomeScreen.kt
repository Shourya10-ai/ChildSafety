package com.childsafety.app.ui.child

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun ChildHomeScreen(
    onSwitchMode: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(text = "Welcome Child!", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(16.dp))
        Text(text = "Protected ID: CHILD-1234", style = MaterialTheme.typography.bodyLarge)
        Spacer(modifier = Modifier.height(32.dp))
        
        Button(
            onClick = { /* SOS Action */ },
            modifier = Modifier.size(120.dp),
            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)
        ) {
            Text("SOS")
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        Button(onClick = { /* Report Action */ }) {
            Text("Report an Issue")
        }
        
        Spacer(modifier = Modifier.height(32.dp))
        OutlinedButton(onClick = onSwitchMode) {
            Text("Switch Mode")
        }
    }
}
