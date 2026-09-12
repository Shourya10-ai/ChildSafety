package com.childsafety.app.ui.adult

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Call
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.room.Room
import com.childsafety.app.data.local.db.AppDatabase
import com.childsafety.app.data.local.db.EmergencyContactEntity
import kotlinx.coroutines.launch

@Composable
fun EmergencyContactsScreen() {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()
    
    val db = remember { 
        Room.databaseBuilder(
            context.applicationContext,
            AppDatabase::class.java,
            "child_safety_db"
        ).fallbackToDestructiveMigration().build()
    }
    
    val dao = db.emergencyContactDao()
    val contacts by dao.getAllContacts().collectAsState(initial = emptyList())

    var showDialog by remember { mutableStateOf(false) }

    Scaffold(
        floatingActionButton = {
            FloatingActionButton(onClick = { showDialog = true }) {
                Icon(Icons.Filled.Add, contentDescription = "Add Contact")
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(contacts) { contact ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(contact.name, style = MaterialTheme.typography.titleMedium)
                            Text(contact.phone, style = MaterialTheme.typography.bodyMedium)
                            if (contact.isPrimary) {
                                Text("Primary", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                            }
                        }
                        IconButton(onClick = {
                            val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:${contact.phone}"))
                            context.startActivity(intent)
                        }) {
                            Icon(Icons.Filled.Call, contentDescription = "Dial", tint = MaterialTheme.colorScheme.primary)
                        }
                    }
                }
            }
        }
    }

    if (showDialog) {
        var newName by remember { mutableStateOf("") }
        var newPhone by remember { mutableStateOf("") }
        var newPrimary by remember { mutableStateOf(false) }

        AlertDialog(
            onDismissRequest = { showDialog = false },
            title = { Text("Add Emergency Contact") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(value = newName, onValueChange = { newName = it }, label = { Text("Name") })
                    OutlinedTextField(value = newPhone, onValueChange = { newPhone = it }, label = { Text("Phone") })
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = newPrimary, onCheckedChange = { newPrimary = it })
                        Text("Primary Contact")
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    if (newName.isNotBlank() && newPhone.isNotBlank()) {
                        coroutineScope.launch {
                            dao.insertContact(EmergencyContactEntity(name = newName, phone = newPhone, isPrimary = newPrimary))
                        }
                        showDialog = false
                    }
                }) {
                    Text("Add")
                }
            },
            dismissButton = {
                TextButton(onClick = { showDialog = false }) { Text("Cancel") }
            }
        )
    }
}
