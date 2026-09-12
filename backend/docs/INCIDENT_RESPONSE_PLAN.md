# Platform Security Breach & Incident Response Plan (IRP)

## 1. Statutory Mandate & Scope
This Incident Response Plan governs cybersecurity events, unauthorized data access, key disclosures, and cryptographic compromises for the **Child Safety Platform**.
- **Regulatory Authority**: Indian Computer Emergency Response Team (CERT-In), Ministry of Electronics and Information Technology (MeitY).
- **Mandatory Reporting Window**: Under CERT-In Cyber Security Directions (No. 20(3)/2022-CERT-In), cybersecurity incidents impacting user data, identity vaults, or critical services **MUST be reported within 6 hours** of notice to `incident@cert-in.org.in`.
- **Data Protection Governance**: Digital Personal Data Protection (DPDP) Act, 2023, Section 8(6) mandatory notification to the Data Protection Board of India and affected data principals (guardians).

---

## 2. Severity Classification Matrix

| Level | Classification | Criteria / Triggers | Response SLA | CERT-In Report Required? |
|---|---|---|---|---|
| **P1 - Critical** | Catastrophic Platform Breach | KMS master key exposure, Identity Vault AES-256 key leak, unauthorized DB dump containing child PII, complete server takeover. | < 15 minutes response | **YES (< 6 Hours)** |
| **P2 - High** | Service Integrity Compromise | Redis / JWT signing key leak, unauthorized moderator session hijacking, Tamper detection alert on Evidence Chain of Custody. | < 30 minutes response | **YES (< 6 Hours)** |
| **P3 - Medium** | Targeted Credential Attack | Brute-force / credential-stuffing attack on adult/moderator accounts, sustained API rate limit threshold triggering. | < 2 hours response | Assessment required |
| **P4 - Low** | Minor Non-PII Anomaly | Isolated software exception, harmless scanning without exploit, certificate expiration warning. | < 24 hours response | No |

---

## 3. Incident Response Protocol: Step-by-Step

### Phase 1: Identification & Initial Triage (< 15 mins)
1. **Trigger Alert**:
   - Automated SIEM/Log alert or moderator breach report.
   - Evidence Chain of Custody integrity failure (`verify_evidence_chain_of_custody` returns `is_valid: False`).
2. **Declare Incident Level**:
   - Lead Security Engineer and Incident Commander declare P1/P2/P3.
   - Start Incident Log (`INCIDENT-<YYYYMMDD>-<SEQ>`).

---

### Phase 2: Immediate Technical Containment (< 30 mins)

#### A. Global Token Invalidation
In the event of a JWT secret leak or moderator credential hijacking, immediately trigger the Global Token Revocation Epoch:
```python
from app.core.security import emergency_revoke_all_tokens
# Invalidates all active access and refresh tokens across all clusters
await emergency_revoke_all_tokens(redis_client)
```
*Effect*: Every active JWT session across web and mobile is instantly terminated. Clients are forced to re-authenticate with multi-factor verification.

#### B. API Gateway Lockdown
Temporarily isolate external traffic or place non-emergency endpoints in read-only maintenance:
```bash
# Set maintenance mode flag in Redis
redis-cli SET system:maintenance_mode "true"
```

#### C. KMS Key Rotation & Identity Vault Re-Encryption
If master data encryption keys are compromised:
1. Generate new DEK/KEK in Hardware Security Module (HSM) or AWS KMS.
2. Execute vault re-encryption script:
   - Reads existing AES-256-GCM ciphertext using old key.
   - Decrypts in secure volatile memory.
   - Re-encrypts with new 256-bit key and updates versioned ciphertext headers.
3. Securely destroy compromised key material in accordance with NIST SP 800-88.

---

### Phase 3: Evidence & Forensic Preservation
1. **Freeze System State**:
   - Capture volatile memory snapshot (RAM dump).
   - Export immutable `evidence_chain_of_custody` ledger to an offline, write-once-read-many (WORM) storage bucket with legal hold.
2. **Audit Trail Verification**:
   - Run verification query:
     ```sql
     SELECT verify_evidence_chain_of_custody(id) FROM evidences;
     ```
   - Identify the exact block and sequence number where any unauthorized modification was attempted.

---

### Phase 4: Statutory Reporting (Within 6 Hours)

#### CERT-In Notification Template
Send encrypted PGP email to `incident@cert-in.org.in`:
- **Subject**: `[INCIDENT REPORT] Child Safety Platform - Cybersecurity Incident Notice`
- **Body**:
  1. Time and date of incident detection (UTC & IST)
  2. Nature of incident (e.g., unauthorized access attempt, credential stuffing, cryptographic revocation)
  3. Systems and services affected
  4. Perimeter containment measures executed (Token revocation epoch, API rate limiting)
  5. Preliminary assessment of compromised records (Zero unencrypted PII accessed due to AES-256 Identity Vault)
  6. Point of contact: Incident Commander (`security@childsafety.org.in`)

---

### Phase 5: Post-Incident Remediation & Recovery
1. Rotate all database credentials, Redis access keys, and server SSL/TLS certificates.
2. Review false-positive and rate-limiting telemetry to patch vulnerability vectors.
3. Conduct Root Cause Analysis (RCA) within 72 hours and archive in post-mortem vault.
