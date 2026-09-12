package com.childsafety.app.ui.shared

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.childsafety.app.ui.mode.SharedProfileSwitcher
import com.childsafety.app.ui.child.ChildHomeScreen
import com.childsafety.app.ui.adult.AdultHomeScreen

@Composable
fun SharedHomeScreen(
    onSwitchMode: () -> Unit
) {
    var isAdultSession by remember { mutableStateOf(false) }

    Column(modifier = Modifier.fillMaxSize()) {
        SharedProfileSwitcher(
            isAdultSession = isAdultSession,
            onSwitchToChild = { isAdultSession = false },
            onSwitchToAdult = { 
                // In real app, prompt for PIN or Biometrics here
                isAdultSession = true 
            }
        )
        
        Box(modifier = Modifier.weight(1f)) {
            if (isAdultSession) {
                AdultHomeScreen(onAddChild = {})
            } else {
                ChildHomeScreen(onSwitchMode = onSwitchMode)
            }
        }
    }
}
