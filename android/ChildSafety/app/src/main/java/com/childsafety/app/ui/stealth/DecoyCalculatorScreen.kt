package com.childsafety.app.ui.stealth

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun DecoyCalculatorScreen(
    onUnlock: () -> Unit
) {
    var display by remember { mutableStateOf("0") }
    var inputSequence by remember { mutableStateOf("") }
    var operand1 by remember { mutableStateOf<Double?>(null) }
    var pendingOperator by remember { mutableStateOf<String?>(null) }
    var isNewNumber by remember { mutableStateOf(true) }

    // Secret passcode to unlock Child Safety Platform: "1423="
    val secretCode = "1423="

    fun onDigit(digit: String) {
        inputSequence += digit
        if (isNewNumber || display == "0") {
            display = digit
            isNewNumber = false
        } else {
            display += digit
        }
    }

    fun onOperator(op: String) {
        inputSequence += op
        operand1 = display.toDoubleOrNull()
        pendingOperator = op
        isNewNumber = true
    }

    fun onEquals() {
        inputSequence += "="
        if (inputSequence.endsWith(secretCode)) {
            onUnlock()
            return
        }

        val op1 = operand1
        val op = pendingOperator
        val op2 = display.toDoubleOrNull()

        if (op1 != null && op != null && op2 != null) {
            val result = when (op) {
                "+" -> op1 + op2
                "-" -> op1 - op2
                "×" -> op1 * op2
                "÷" -> if (op2 != 0.0) op1 / op2 else Double.NaN
                else -> op2
            }
            display = if (result.isNaN()) {
                "Error"
            } else if (result == result.toLong().toDouble()) {
                result.toLong().toString()
            } else {
                result.toString()
            }
        }
        operand1 = null
        pendingOperator = null
        isNewNumber = true
    }

    fun onClear() {
        display = "0"
        operand1 = null
        pendingOperator = null
        isNewNumber = true
        inputSequence = ""
    }

    // Decoy Calculator UI - Native calculator appearance
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF1C1C1E))
            .padding(16.dp),
        verticalArrangement = Arrangement.Bottom
    ) {
        // Display area
        Text(
            text = display,
            style = MaterialTheme.typography.displayLarge.copy(
                fontSize = 54.sp,
                fontWeight = FontWeight.Light,
                color = Color.White
            ),
            maxLines = 1,
            textAlign = TextAlign.End,
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 24.dp, end = 12.dp)
        )

        // Keypad Rows
        val buttonSpacing = 12.dp

        val rows = listOf(
            listOf(
                CalcBtn("C", Color(0xFFA5A5A5), Color.Black) { onClear() },
                CalcBtn("±", Color(0xFFA5A5A5), Color.Black) {
                    val cur = display.toDoubleOrNull()
                    if (cur != null) {
                        display = if (cur == cur.toLong().toDouble()) (-cur.toLong()).toString() else (-cur).toString()
                    }
                },
                CalcBtn("%", Color(0xFFA5A5A5), Color.Black) {
                    val cur = display.toDoubleOrNull()
                    if (cur != null) display = (cur / 100.0).toString()
                },
                CalcBtn("÷", Color(0xFFFF9F0A), Color.White) { onOperator("÷") }
            ),
            listOf(
                CalcBtn("7", Color(0xFF333333), Color.White) { onDigit("7") },
                CalcBtn("8", Color(0xFF333333), Color.White) { onDigit("8") },
                CalcBtn("9", Color(0xFF333333), Color.White) { onDigit("9") },
                CalcBtn("×", Color(0xFFFF9F0A), Color.White) { onOperator("×") }
            ),
            listOf(
                CalcBtn("4", Color(0xFF333333), Color.White) { onDigit("4") },
                CalcBtn("5", Color(0xFF333333), Color.White) { onDigit("5") },
                CalcBtn("6", Color(0xFF333333), Color.White) { onDigit("6") },
                CalcBtn("-", Color(0xFFFF9F0A), Color.White) { onOperator("-") }
            ),
            listOf(
                CalcBtn("1", Color(0xFF333333), Color.White) { onDigit("1") },
                CalcBtn("2", Color(0xFF333333), Color.White) { onDigit("2") },
                CalcBtn("3", Color(0xFF333333), Color.White) { onDigit("3") },
                CalcBtn("+", Color(0xFFFF9F0A), Color.White) { onOperator("+") }
            ),
            listOf(
                CalcBtn("0", Color(0xFF333333), Color.White, weight = 2f) { onDigit("0") },
                CalcBtn(".", Color(0xFF333333), Color.White) {
                    if (!display.contains(".")) {
                        display += "."
                        isNewNumber = false
                    }
                },
                CalcBtn("=", Color(0xFFFF9F0A), Color.White) { onEquals() }
            )
        )

        rows.forEach { row ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = buttonSpacing / 2),
                horizontalArrangement = Arrangement.spacedBy(buttonSpacing)
            ) {
                row.forEach { btn ->
                    Button(
                        onClick = btn.onClick,
                        shape = CircleShape,
                        colors = ButtonDefaults.buttonColors(containerColor = btn.bgColor),
                        modifier = Modifier
                            .weight(btn.weight)
                            .height(72.dp),
                        contentPadding = PaddingValues(0.dp)
                    ) {
                        Text(
                            text = btn.label,
                            fontSize = 28.sp,
                            fontWeight = FontWeight.Normal,
                            color = btn.textColor
                        )
                    }
                }
            }
        }
        Spacer(modifier = Modifier.height(16.dp))
    }
}

private data class CalcBtn(
    val label: String,
    val bgColor: Color,
    val textColor: Color,
    val weight: Float = 1f,
    val onClick: () -> Unit
)
