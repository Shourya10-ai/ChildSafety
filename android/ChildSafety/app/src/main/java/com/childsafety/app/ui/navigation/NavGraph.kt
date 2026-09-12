package com.childsafety.app.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.childsafety.app.ui.auth.LoginScreen
import com.childsafety.app.ui.auth.RegisterScreen
import com.childsafety.app.ui.WelcomeScreen

object Routes {
    const val WELCOME = "welcome"
    const val LOGIN = "login"
    const val REGISTER = "register"
    // These will be added in Phase 3:
    const val CHILD_HOME = "child_home"
    const val ADULT_HOME = "adult_home"
    const val SHARED_HOME = "shared_home"
    const val MODE_SELECTION = "mode_selection"
}

@Composable
fun AppNavGraph(startDestination: String = Routes.WELCOME) {
    val navController = rememberNavController()
    NavHost(navController = navController, startDestination = startDestination) {
        composable(Routes.WELCOME) {
            WelcomeScreen(
                onGetStarted = { navController.navigate(Routes.LOGIN) }
            )
        }
        composable(Routes.LOGIN) {
            LoginScreen(
                onLoginSuccess = { role ->
                    navController.navigate(Routes.MODE_SELECTION) {
                        popUpTo(Routes.LOGIN) { inclusive = true }
                    }
                },
                onNavigateToRegister = { navController.navigate(Routes.REGISTER) }
            )
        }
        composable(Routes.REGISTER) {
            RegisterScreen(
                onRegisterSuccess = { role ->
                    navController.navigate(Routes.MODE_SELECTION) {
                        popUpTo(Routes.REGISTER) { inclusive = true }
                    }
                },
                onNavigateToLogin = { navController.popBackStack() }
            )
        }
        composable(Routes.MODE_SELECTION) {
            // Placeholder until Phase 3
            WelcomeScreen()
        }
    }
}
