package com.childsafety.app.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.childsafety.app.ui.WelcomeScreen
import com.childsafety.app.ui.auth.LoginScreen
import com.childsafety.app.ui.auth.RegisterScreen
import com.childsafety.app.ui.mode.ModeSelectionScreen
import com.childsafety.app.ui.child.*
import com.childsafety.app.ui.adult.*
import com.childsafety.app.ui.shared.SharedHomeScreen
import com.childsafety.app.ui.stealth.DecoyCalculatorScreen
import com.childsafety.app.ui.common.AppBottomNav
import com.childsafety.app.ui.common.AppTopBar
import com.childsafety.app.ui.common.NavItems

object Routes {
    const val WELCOME = "welcome"
    const val LOGIN = "login"
    const val REGISTER = "register"
    const val MODE_SELECTION = "mode_selection"
    const val DECOY_CALCULATOR = "decoy_calculator"

    const val CHILD_HOME = "child_home"
    const val CHILD_REPORT = "child_report"
    const val CHILD_CHAT = "child_chat"
    const val CHILD_TIPS = "child_tips"
    const val CHILD_SETTINGS = "child_settings"
    
    const val ADULT_HOME = "adult_home"
    const val ADULT_LINK_CHILD = "adult_link_child"
    const val ADULT_ALERTS = "adult_alerts"
    const val ADULT_CONTACTS = "adult_contacts"
    
    const val SHARED_HOME = "shared_home"

    const val MISSING_CHILD_ALERTS = "missing_child_alerts"
    const val REPORT_MISSING_CHILD = "report_missing_child"
    const val DPDP_RIGHTS = "dpdp_rights"
}

@Composable
fun AppNavGraph(startDestination: String = Routes.WELCOME) {
    val navController = rememberNavController()
    val backStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = backStackEntry?.destination?.route

    val isAuthOrWelcome = currentRoute in listOf(
        Routes.WELCOME,
        Routes.LOGIN,
        Routes.REGISTER,
        Routes.MODE_SELECTION,
        Routes.DECOY_CALCULATOR
    )

    val isChildMode = currentRoute?.startsWith("child") == true
    val isAdultMode = currentRoute?.startsWith("adult") == true

    Scaffold(
        topBar = {
            if (!isAuthOrWelcome) {
                AppTopBar(
                    title = "Child Safety",
                    mode = when {
                        isChildMode -> "Child Mode"
                        isAdultMode -> "Adult Mode"
                        else -> "Shared Mode"
                    },
                    onBackClick = if (navController.previousBackStackEntry != null) {
                        { navController.popBackStack() }
                    } else null,
                    onSettingsClick = {
                        if (isChildMode) {
                            navController.navigate(Routes.CHILD_SETTINGS)
                        } else {
                            navController.navigate(Routes.MODE_SELECTION)
                        }
                    },
                    onQuickExitClick = {
                        navController.navigate(Routes.DECOY_CALCULATOR) {
                            popUpTo(0) { inclusive = true }
                        }
                    }
                )
            }
        },
        bottomBar = {
            if (!isAuthOrWelcome && currentRoute != Routes.SHARED_HOME && currentRoute != Routes.CHILD_SETTINGS && currentRoute != Routes.ADULT_LINK_CHILD) {
                val navItems = if (isChildMode) NavItems.ChildItems else NavItems.AdultItems
                AppBottomNav(
                    items = navItems,
                    currentRoute = currentRoute,
                    onNavigate = { route ->
                        navController.navigate(route) {
                            popUpTo(navController.graph.startDestinationId) { saveState = true }
                            launchSingleTop = true
                            restoreState = true
                        }
                    }
                )
            }
        }
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = startDestination,
            modifier = if (isAuthOrWelcome) Modifier else Modifier.padding(padding)
        ) {
            // Welcome & Auth Flows
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
                ModeSelectionScreen(
                    onModeSelected = { mode ->
                        val targetRoute = when (mode) {
                            "CHILD" -> Routes.CHILD_HOME
                            "ADULT" -> Routes.ADULT_HOME
                            "SHARED" -> Routes.SHARED_HOME
                            else -> Routes.CHILD_HOME
                        }
                        navController.navigate(targetRoute) {
                            popUpTo(Routes.MODE_SELECTION) { inclusive = true }
                        }
                    }
                )
            }

            // Shared Device Route
            composable(Routes.SHARED_HOME) {
                SharedHomeScreen(
                    onNavigateToReport = { navController.navigate(Routes.CHILD_REPORT) },
                    onNavigateToChat = { navController.navigate(Routes.CHILD_CHAT) },
                    onNavigateToTips = { navController.navigate(Routes.CHILD_TIPS) },
                    onNavigateToLinkChild = { navController.navigate(Routes.ADULT_LINK_CHILD) },
                    onNavigateToAlerts = { navController.navigate(Routes.ADULT_ALERTS) },
                    onNavigateToContacts = { navController.navigate(Routes.ADULT_CONTACTS) },
                    onNavigateToSettings = { navController.navigate(Routes.MODE_SELECTION) }
                )
            }

            // Child Routes
            composable(Routes.CHILD_HOME) {
                ChildHomeScreen(
                    onNavigateToReport = { navController.navigate(Routes.CHILD_REPORT) },
                    onNavigateToChat = { navController.navigate(Routes.CHILD_CHAT) },
                    onNavigateToTips = { navController.navigate(Routes.CHILD_TIPS) },
                    onNavigateToMissingAlerts = { navController.navigate(Routes.MISSING_CHILD_ALERTS) },
                    onSwitchMode = {
                        navController.navigate(Routes.MODE_SELECTION) {
                            popUpTo(Routes.CHILD_HOME) { inclusive = true }
                        }
                    }
                )
            }
            composable(Routes.CHILD_REPORT) {
                ChildReportScreen(onNavigateBack = { navController.popBackStack() })
            }
            composable(Routes.CHILD_CHAT) {
                ChildChatScreen()
            }
            composable(Routes.CHILD_TIPS) {
                SafetyTipsScreen()
            }
            composable(Routes.CHILD_SETTINGS) {
                ChildSettingsScreen(
                    onExitChildMode = {
                        navController.navigate(Routes.MODE_SELECTION) {
                            popUpTo(Routes.CHILD_HOME) { inclusive = true }
                        }
                    },
                    onQuickStealthExit = {
                        navController.navigate(Routes.DECOY_CALCULATOR) {
                            popUpTo(0) { inclusive = true }
                        }
                    },
                    onNavigateToDpdpRights = {
                        navController.navigate(Routes.DPDP_RIGHTS)
                    }
                )
            }
            composable(Routes.DECOY_CALCULATOR) {
                DecoyCalculatorScreen(
                    onUnlock = {
                        navController.navigate(Routes.MODE_SELECTION) {
                            popUpTo(Routes.DECOY_CALCULATOR) { inclusive = true }
                        }
                    }
                )
            }

            // Adult Routes
            composable(Routes.ADULT_HOME) {
                AdultHomeScreen(
                    onNavigateToLinkChild = { navController.navigate(Routes.ADULT_LINK_CHILD) },
                    onNavigateToAlerts = { navController.navigate(Routes.ADULT_ALERTS) },
                    onNavigateToContacts = { navController.navigate(Routes.ADULT_CONTACTS) },
                    onNavigateToSettings = { navController.navigate(Routes.MODE_SELECTION) },
                    onNavigateToReportMissingChild = { navController.navigate(Routes.REPORT_MISSING_CHILD) },
                    onNavigateToMissingChildAlerts = { navController.navigate(Routes.MISSING_CHILD_ALERTS) },
                    onNavigateToDpdpRights = { navController.navigate(Routes.DPDP_RIGHTS) }
                )
            }
            composable(Routes.ADULT_LINK_CHILD) {
                LinkChildScreen(onNavigateBack = { navController.popBackStack() })
            }
            composable(Routes.ADULT_ALERTS) {
                AdultAlertsScreen()
            }
            composable(Routes.ADULT_CONTACTS) {
                EmergencyContactsScreen()
            }

            // Phase 9: Missing Child Network & DPDP Act
            composable(Routes.MISSING_CHILD_ALERTS) {
                MissingChildAlertsScreen(onNavigateBack = { navController.popBackStack() })
            }
            composable(Routes.REPORT_MISSING_CHILD) {
                MissingChildReportScreen(onNavigateBack = { navController.popBackStack() })
            }
            composable(Routes.DPDP_RIGHTS) {
                DpdpRightsScreen(onNavigateBack = { navController.popBackStack() })
            }
        }
    }
}
