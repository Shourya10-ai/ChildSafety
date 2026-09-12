package com.childsafety.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.childsafety.app.security.TokenManager
import com.childsafety.app.ui.navigation.AppNavGraph
import com.childsafety.app.ui.navigation.Routes
import com.childsafety.app.ui.theme.ChildSafetyTheme
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject lateinit var tokenManager: TokenManager

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            ChildSafetyTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val startDestination = if (tokenManager.isLoggedIn()) {
                        Routes.MODE_SELECTION // Will be replaced with role-based routing in Phase 3
                    } else {
                        Routes.WELCOME
                    }
                    AppNavGraph(startDestination = startDestination)
                }
            }
        }
    }
}
