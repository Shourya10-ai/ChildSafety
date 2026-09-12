package com.childsafety.app.ui.common

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.vector.ImageVector

data class BottomNavItem(
    val title: String,
    val icon: ImageVector,
    val route: String
)

@Composable
fun AppBottomNav(
    items: List<BottomNavItem>,
    currentRoute: String?,
    onNavigate: (String) -> Unit
) {
    NavigationBar {
        items.forEach { item ->
            NavigationBarItem(
                selected = currentRoute == item.route,
                onClick = { onNavigate(item.route) },
                icon = { Icon(imageVector = item.icon, contentDescription = item.title) },
                label = { Text(item.title) }
            )
        }
    }
}

object NavItems {
    val ChildItems = listOf(
        BottomNavItem("Home", Icons.Filled.Home, "child_home"),
        BottomNavItem("Report", Icons.Filled.Warning, "child_report"),
        BottomNavItem("Chat", Icons.Filled.MailOutline, "child_chat"),
        BottomNavItem("Tips", Icons.Filled.Info, "child_tips")
    )

    val AdultItems = listOf(
        BottomNavItem("Dashboard", Icons.Filled.Home, "adult_home"),
        BottomNavItem("Children", Icons.Filled.Person, "adult_link_child"),
        BottomNavItem("Alerts", Icons.Filled.Notifications, "adult_alerts"),
        BottomNavItem("Contacts", Icons.Filled.Call, "adult_contacts")
    )
}
