package com.childsafety.app.ui.auth

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.location.Geocoder
import android.location.Location
import android.location.LocationManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import java.util.Locale
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RegisterScreen(
    onRegisterSuccess: (role: String) -> Unit,
    onNavigateToLogin: () -> Unit,
    viewModel: AuthViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val fullName by viewModel.fullNameState.collectAsState()
    val email by viewModel.emailState.collectAsState()
    val password by viewModel.passwordState.collectAsState()
    val confirmPassword by viewModel.confirmPasswordState.collectAsState()
    val phone by viewModel.phoneState.collectAsState()
    val selectedRole by viewModel.selectedRole.collectAsState()
    val isPasswordVisible by viewModel.isPasswordVisible.collectAsState()

    // Location & Setup Path state
    val stateVal by viewModel.stateState.collectAsState()
    val districtVal by viewModel.districtState.collectAsState()
    val pinCodeVal by viewModel.pinCodeState.collectAsState()
    val dobVal by viewModel.dobState.collectAsState()
    val setupPathVal by viewModel.childSetupPath.collectAsState()
    val parentEmailVal by viewModel.parentEmailState.collectAsState()
    val schoolNameVal by viewModel.schoolNameState.collectAsState()
    val locationDetectedMsg by viewModel.locationDetectedMessage.collectAsState()
    val locationErrorMsg by viewModel.locationErrorMessage.collectAsState()
    val isDetectingLocation by viewModel.isDetectingLocation.collectAsState()
    val context = LocalContext.current

    fun processLocation(loc: Location) {
        try {
            val geocoder = Geocoder(context, Locale.getDefault())
            @Suppress("DEPRECATION")
            val addresses = geocoder.getFromLocation(loc.latitude, loc.longitude, 1)
            if (!addresses.isNullOrEmpty()) {
                val addr = addresses[0]
                val state = addr.adminArea
                val district = addr.subAdminArea ?: addr.locality ?: addr.subLocality
                val pinCode = addr.postalCode
                if (!state.isNullOrBlank() && !district.isNullOrBlank()) {
                    viewModel.applyDetectedLocation(
                        lat = loc.latitude,
                        lng = loc.longitude,
                        state = state,
                        district = district,
                        pinCode = pinCode
                    )
                    viewModel.isDetectingLocation.value = false
                    return
                }
            }
        } catch (_: Exception) {}
        // If native Geocoder fails or returns incomplete info, query backend live reverse geocoding API
        viewModel.reverseGeocodeAndSet(loc.latitude, loc.longitude)
    }

    fun fetchDeviceLocationAndFill() {
        viewModel.isDetectingLocation.value = true
        val fusedClient = LocationServices.getFusedLocationProviderClient(context)
        try {
            val cancellationTokenSource = CancellationTokenSource()
            fusedClient.getCurrentLocation(Priority.PRIORITY_HIGH_ACCURACY, cancellationTokenSource.token)
                .addOnSuccessListener { liveLoc ->
                    if (liveLoc != null) {
                        processLocation(liveLoc)
                    } else {
                        fusedClient.lastLocation.addOnSuccessListener { lastLoc ->
                            if (lastLoc != null) {
                                processLocation(lastLoc)
                            } else {
                                val lm = context.getSystemService(Context.LOCATION_SERVICE) as? LocationManager
                                val netLoc = try {
                                    lm?.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
                                        ?: lm?.getLastKnownLocation(LocationManager.GPS_PROVIDER)
                                } catch (_: SecurityException) { null }

                                if (netLoc != null) {
                                    processLocation(netLoc)
                                } else {
                                    // Query Ipstack via backend (pass null coords so it uses client IP)
                                    viewModel.reverseGeocodeAndSet(null, null)
                                }
                            }
                        }.addOnFailureListener {
                            viewModel.reverseGeocodeAndSet(null, null)
                        }
                    }
                }
                .addOnFailureListener {
                    viewModel.reverseGeocodeAndSet(null, null)
                }
        } catch (_: SecurityException) {
            viewModel.reverseGeocodeAndSet(null, null)
        } catch (_: Exception) {
            viewModel.reverseGeocodeAndSet(null, null)
        }
    }

    val locationPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val granted = permissions[Manifest.permission.ACCESS_FINE_LOCATION] == true ||
                      permissions[Manifest.permission.ACCESS_COARSE_LOCATION] == true
        if (granted) {
            fetchDeviceLocationAndFill()
        } else {
            // Permission denied: geolocate via IP geolocation on backend
            viewModel.reverseGeocodeAndSet(null, null)
        }
    }

    LaunchedEffect(uiState.isSuccess) {
        if (uiState.isSuccess) {
            uiState.userRole?.let { onRegisterSuccess(it) }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Account Setup & Registration") },
                navigationIcon = {
                    IconButton(onClick = onNavigateToLogin) {
                        Icon(imageVector = Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 20.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            item {
                Spacer(modifier = Modifier.height(8.dp))

                // 1. Role Selector
                Text("Select Account Type", style = MaterialTheme.typography.titleMedium, modifier = Modifier.fillMaxWidth())
                Spacer(modifier = Modifier.height(8.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    FilterChip(
                        selected = selectedRole == "child",
                        onClick = { viewModel.selectedRole.value = "child" },
                        label = { Text("🧒 Child Profile") },
                        modifier = Modifier.weight(1f)
                    )
                    FilterChip(
                        selected = selectedRole == "adult",
                        onClick = { viewModel.selectedRole.value = "adult" },
                        label = { Text("👨 Adult Guardian") },
                        modifier = Modifier.weight(1f)
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                // 2. Child Sub-Path: Domestic/Solo vs Collaborative
                if (selectedRole == "child") {
                    Text(
                        "How are you setting up this profile?",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.fillMaxWidth()
                    )
                    Spacer(modifier = Modifier.height(8.dp))

                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { viewModel.childSetupPath.value = "SOLO" },
                        shape = RoundedCornerShape(12.dp),
                        border = if (setupPathVal == "SOLO") BorderStroke(2.dp, MaterialTheme.colorScheme.error) else null,
                        colors = CardDefaults.cardColors(
                            containerColor = if (setupPathVal == "SOLO") MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.4f) else MaterialTheme.colorScheme.surfaceVariant
                        )
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text("🔴 Solo / Domestic Danger", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.error)
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                "I am setting this up alone. Household adults are bypassed and will NOT receive my alerts. A local safety protector will be assigned directly.",
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { viewModel.childSetupPath.value = "COLLABORATIVE" },
                        shape = RoundedCornerShape(12.dp),
                        border = if (setupPathVal == "COLLABORATIVE") BorderStroke(2.dp, MaterialTheme.colorScheme.primary) else null,
                        colors = CardDefaults.cardColors(
                            containerColor = if (setupPathVal == "COLLABORATIVE") MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.4f) else MaterialTheme.colorScheme.surfaceVariant
                        )
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text("🟢 With a Parent / Guardian", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                "My parent or trusted adult is helping me. Link directly to their account now.",
                                style = MaterialTheme.typography.bodySmall
                            )
                        }
                    }

                    // If Collaborative, ask for Parent Email
                    if (setupPathVal == "COLLABORATIVE") {
                        Spacer(modifier = Modifier.height(12.dp))
                        OutlinedTextField(
                            value = parentEmailVal,
                            onValueChange = { viewModel.parentEmailState.value = it },
                            label = { Text("Parent / Guardian's Account Email") },
                            placeholder = { Text("parent@example.com") },
                            modifier = Modifier.fillMaxWidth(),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                            singleLine = true,
                            leadingIcon = { Icon(Icons.Default.Person, contentDescription = null) }
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                }

                Divider()
                Spacer(modifier = Modifier.height(16.dp))

                // 3. Mandatory Base Info Section
                Text("Base Information", style = MaterialTheme.typography.titleMedium, modifier = Modifier.fillMaxWidth())
                Spacer(modifier = Modifier.height(12.dp))

                OutlinedTextField(
                    value = fullName,
                    onValueChange = { viewModel.fullNameState.value = it },
                    label = { Text("Full Name") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(12.dp))

                OutlinedTextField(
                    value = email,
                    onValueChange = { viewModel.emailState.value = it },
                    label = {
                        Text(if (selectedRole == "child" && setupPathVal == "SOLO") "Personal Private Email (Not Family Email)" else "Email Address")
                    },
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(12.dp))

                OutlinedTextField(
                    value = password,
                    onValueChange = { viewModel.passwordState.value = it },
                    label = { Text("Password (Min 8 chars, 1 uppercase, 1 digit)") },
                    modifier = Modifier.fillMaxWidth(),
                    visualTransformation = if (isPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                    trailingIcon = {
                        val image = if (isPasswordVisible) Icons.Default.Visibility else Icons.Default.VisibilityOff
                        IconButton(onClick = { viewModel.togglePasswordVisibility() }) {
                            Icon(imageVector = image, contentDescription = "Toggle password visibility")
                        }
                    },
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(12.dp))

                OutlinedTextField(
                    value = confirmPassword,
                    onValueChange = { viewModel.confirmPasswordState.value = it },
                    label = { Text("Confirm Password") },
                    modifier = Modifier.fillMaxWidth(),
                    visualTransformation = if (isPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                    singleLine = true
                )
                Spacer(modifier = Modifier.height(12.dp))

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    OutlinedTextField(
                        value = phone,
                        onValueChange = { viewModel.phoneState.value = it },
                        label = { Text("Phone") },
                        modifier = Modifier.weight(1f),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = dobVal,
                        onValueChange = { viewModel.dobState.value = it },
                        label = { Text("DOB (YYYY-MM-DD)") },
                        placeholder = { Text("2012-05-15") },
                        modifier = Modifier.weight(1f),
                        singleLine = true
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))

                // 4. Mandatory Location Info (For Jurisdictional ID & Local Moderator Assignment)
                Text(
                    "Jurisdictional Location (For Local Protector Linking)",
                    style = MaterialTheme.typography.titleMedium,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Auto-detect your location with 1-tap GPS, or enter details below.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(8.dp))

                Button(
                    onClick = {
                        val fineGranted = ContextCompat.checkSelfPermission(
                            context,
                            Manifest.permission.ACCESS_FINE_LOCATION
                        ) == PackageManager.PERMISSION_GRANTED
                        val coarseGranted = ContextCompat.checkSelfPermission(
                            context,
                            Manifest.permission.ACCESS_COARSE_LOCATION
                        ) == PackageManager.PERMISSION_GRANTED

                        if (fineGranted || coarseGranted) {
                            fetchDeviceLocationAndFill()
                        } else {
                            locationPermissionLauncher.launch(
                                arrayOf(
                                    Manifest.permission.ACCESS_FINE_LOCATION,
                                    Manifest.permission.ACCESS_COARSE_LOCATION
                                )
                            )
                        }
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.secondaryContainer,
                        contentColor = MaterialTheme.colorScheme.onSecondaryContainer
                    ),
                    shape = RoundedCornerShape(10.dp),
                    enabled = !isDetectingLocation
                ) {
                    if (isDetectingLocation) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(18.dp),
                            strokeWidth = 2.dp,
                            color = MaterialTheme.colorScheme.onSecondaryContainer
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Detecting GPS Location...", fontWeight = FontWeight.Medium)
                    } else {
                        Icon(Icons.Filled.Place, contentDescription = "Auto Detect Location", modifier = Modifier.size(20.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("📍 Auto-Detect GPS Location (1-Tap)", fontWeight = FontWeight.SemiBold)
                    }
                }

                if (!locationDetectedMsg.isNullOrEmpty()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.6f)
                        ),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Filled.CheckCircle,
                                contentDescription = "Location Set",
                                tint = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Auto-Detected: $locationDetectedMsg",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onPrimaryContainer,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }

                if (!locationErrorMsg.isNullOrEmpty()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.7f)
                        ),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Filled.Warning,
                                contentDescription = "Location Error",
                                tint = MaterialTheme.colorScheme.error,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = locationErrorMsg!!,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onErrorContainer,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(12.dp))

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    OutlinedTextField(
                        value = stateVal,
                        onValueChange = { viewModel.stateState.value = it },
                        label = { Text("State / UT") },
                        placeholder = { Text("e.g. Maharashtra, Delhi") },
                        modifier = Modifier.weight(1f),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = districtVal,
                        onValueChange = { viewModel.districtState.value = it },
                        label = { Text("District / City") },
                        placeholder = { Text("e.g. Mumbai, South Delhi") },
                        modifier = Modifier.weight(1f),
                        singleLine = true
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    OutlinedTextField(
                        value = pinCodeVal,
                        onValueChange = { viewModel.pinCodeState.value = it },
                        label = { Text("PIN Code (6 digits)") },
                        modifier = Modifier.weight(1f),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true
                    )
                    if (selectedRole == "child") {
                        OutlinedTextField(
                            value = schoolNameVal,
                            onValueChange = { viewModel.schoolNameState.value = it },
                            label = { Text("School Name (Optional)") },
                            modifier = Modifier.weight(1f),
                            singleLine = true
                        )
                    }
                }

                Spacer(modifier = Modifier.height(20.dp))

                uiState.error?.let {
                    Text(text = it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium)
                    Spacer(modifier = Modifier.height(12.dp))
                }

                Button(
                    onClick = { viewModel.register() },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(50.dp),
                    enabled = !uiState.isLoading
                ) {
                    if (uiState.isLoading) {
                        CircularProgressIndicator(modifier = Modifier.size(24.dp), color = MaterialTheme.colorScheme.onPrimary)
                    } else {
                        Text("Complete Registration & Setup", fontSize = 16.sp)
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))
                TextButton(onClick = onNavigateToLogin) {
                    Text("Already have an account? Login")
                }
                Spacer(modifier = Modifier.height(32.dp))
            }
        }
    }
}
