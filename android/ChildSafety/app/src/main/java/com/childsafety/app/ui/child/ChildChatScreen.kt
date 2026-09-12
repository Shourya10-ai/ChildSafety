package com.childsafety.app.ui.child

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChildChatScreen() {
    var message by remember { mutableStateOf("") }
    var messages by remember { mutableStateOf(listOf(
        Pair("Hello! I am your safety helper. How can I help you today?", false)
    )) }

    val suggestions = listOf(
        "Someone asking for photos",
        "Told to keep a secret",
        "Wants to move to WhatsApp",
        "Someone bullying me",
        "I feel unsafe at home"
    )

    val botResponses = mapOf(
        "Someone asking for photos" to "🚨 Never send photos you aren't comfortable with. Under Indian law (POCSO Act), asking children for photos is illegal. Would you like to file a confidential report with our child protectors?",
        "Told to keep a secret" to "🛡️ Real friends and safe adults will NEVER ask you to keep secrets from the people who love and protect you. If someone says 'kisi ko mat batana', tell a trusted adult immediately.",
        "Wants to move to WhatsApp" to "⚠️ Moving from a game or social app to private messaging is a common tactic used to isolate kids. Stay on monitored channels and do not share your private phone number.",
        "Someone bullying me" to "💪 Nobody has the right to bully, insult, or threaten to leak your messages. You are not alone. Take screenshots of the messages and submit a report here.",
        "I feel unsafe at home" to "💛 If you are facing harm or abuse at home, you can nominate a Trusted Adult (like an aunt or teacher) in Settings who will receive your alerts safely, or press the discreet Duress SOS."
    )

    Column(modifier = Modifier.fillMaxSize()) {
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(messages) { msg ->
                val isUser = msg.second
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
                ) {
                    Surface(
                        shape = RoundedCornerShape(16.dp),
                        color = if (isUser) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.surfaceVariant
                    ) {
                        Text(
                            text = msg.first,
                            modifier = Modifier.padding(12.dp),
                            color = if (isUser) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }

        LazyRow(
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(suggestions) { suggestion ->
                SuggestionChip(
                    onClick = {
                        messages = messages + Pair(suggestion, true)
                        val reply = botResponses[suggestion] ?: "I'm here to help. Can you tell me more about what happened?"
                        messages = messages + Pair(reply, false)
                    },
                    label = { Text(suggestion) }
                )
            }
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = message,
                onValueChange = { message = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("Type a message or question...") },
                shape = RoundedCornerShape(24.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            IconButton(
                onClick = {
                    if (message.isNotBlank()) {
                        val userText = message
                        messages = messages + Pair(userText, true)
                        message = ""

                        val lower = userText.lowercase()
                        val response = when {
                            lower.contains("secret") || lower.contains("batana") || lower.contains("mat bata") ->
                                "🚨 If someone asked you to keep a secret, please tell a trusted adult or submit a report. We are here to keep you safe!"
                            lower.contains("photo") || lower.contains("pic") || lower.contains("clothes") ->
                                "⚠️ Warning: Never share personal photos online. If anyone asks for photos, you can block them and file a report right now."
                            lower.contains("whatsapp") || lower.contains("number") ->
                                "🔒 Protect your privacy! Avoid sharing your phone number or moving conversations to private messaging apps."
                            else ->
                                "Thank you for sharing with me. You are safe here. If you need urgent help, tap the SOS button or report an incident."
                        }
                        messages = messages + Pair(response, false)
                    }
                },
                modifier = Modifier
                    .background(MaterialTheme.colorScheme.primary, RoundedCornerShape(24.dp))
            ) {
                Icon(Icons.Default.Send, contentDescription = "Send", tint = MaterialTheme.colorScheme.onPrimary)
            }
        }
    }
}
