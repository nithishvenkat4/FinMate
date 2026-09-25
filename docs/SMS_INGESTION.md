# FinMate — SMS Transaction Tracking Integration Guide

This guide documents the native Android SMS ingestion application (`FinMateSMS`) and its integration with the existing FinMate FastAPI backend.

---

## 1. System Overview & Architecture

The FinMate SMS client runs as a background service on Android to detect financial transactions from authorized bank SMS notifications. It parses transactions deterministically on-device, buffers them in a local Room database queue, and synchronizes them with the FinMate FastAPI backend whenever internet connectivity is available.

```
+-------------------------------------------------------------------------------+
|                             Android Client (FinMateSMS)                      |
|                                                                               |
|   Incoming SMS                                                                |
|        │                                                                      |
|        ▼                                                                      |
|   [SmsReceiver] ──────► Sender in Allowed List? (HDFCBK, SBIINB, etc.)        |
|        │                       │                                              |
|        ▼                       └─► NO: Ignored immediately                    |
|   [SmsTransactionParser]                                                      |
|        │ Extracts: Amount (>0), Date, Type (Debit/Credit), Deterministic Hash |
|        ▼                                                                      |
|   [Room Database] ───► Stores `PendingTransaction` (Status: PENDING)          |
|        │                                                                      |
|        ▼                                                                      |
|   [SyncWorker] (WorkManager with NetworkType.CONNECTED constraint)            |
+--------│----------------------------------------------------------------------+
         │ POST /api/v1/transactions/from-sms (JSON)
         ▼
+-------------------------------------------------------------------------------+
|                             FinMate FastAPI Backend                           |
|                                                                               |
|   1. Payload Validation (Amount > 0, valid date, source = "sms")              |
|   2. Duplicate Prevention Check (source_type="sms" AND source_ref=sms_hash)   |
|   3. PostgreSQL/SQLite Ledger Insertion                                       |
|   4. HTTP 201 Created (or HTTP 409 Conflict if already ingested)              |
+--------│----------------------------------------------------------------------+
         │
         ▼
+-------------------------------------------------------------------------------+
|                             FinMate Web Application                           |
|                                                                               |
|   Displays seamlessly in existing Transactions Ledger:                        |
|   "25 Sept 2026 | SMS Transaction | Other | Expense | -₹850.00"               |
+-------------------------------------------------------------------------------+
```

---

## 2. Component Specifications

### 2.1 Android Application (`android/FinMateSMS`)
- **Location**: `d:\FinMate\android\FinMateSMS`
- **Package**: `com.finmate.sms`
- **Target SDK**: Android 14 (API 34), Min SDK: Android 7.0 (API 24)
- **Language**: Kotlin 1.9+
- **Persistence**: AndroidX Room 2.6.1 (`PendingTransaction` table with unique index on `sms_hash`)
- **Background Execution**: AndroidX WorkManager 2.9.0 (`SyncWorker` with network connectivity constraints)
- **Networking**: Retrofit 2.11.0 + OkHttp 4.12.0
- **UI**: Material Design 3, live status counters, toggle switch, allowed senders configuration.

### 2.2 Backend Endpoint (`backend/app/api/v1/endpoints/transactions.py`)
- **Endpoint**: `POST /api/v1/transactions/from-sms`
- **Payload Schema**:
  ```json
  {
    "amount": 850.00,
    "transaction_date": "2026-09-25",
    "type": "expense",
    "category": "Other",
    "description": "SMS Transaction",
    "source": "sms",
    "sender": "HDFCBK",
    "sms_hash": "a1b2c3d4e5f67890abcdef1234567890"
  }
  ```
- **Responses**:
  - `201 Created`: Transaction inserted and returned with generated `id`.
  - `409 Conflict`: Duplicate transaction detected with code `DUPLICATE_TRANSACTION`.
  - `422 Unprocessable Entity`: Validation failure (e.g. `amount <= 0` or missing required fields).

---

## 3. Privacy & Security Guarantees

1. **Zero Raw SMS Uploads**: The full text of the SMS message is **never** sent to the server. Only structured fields (`amount`, `transaction_date`, `type`, `sender`, `sms_hash`) are transmitted.
2. **Strict OTP & PIN Discard**: Messages containing one-time passwords (`otp`, `verification code`, `secret code`) are explicitly identified and discarded before any transaction parsing occurs.
3. **No Database Direct Access**: The Android client connects only to the public HTTP REST API and never maintains direct connections or credentials to PostgreSQL.
4. **Sender Whitelisting**: Messages from senders not in the configured allowed senders list are discarded immediately at the broadcast level.

---

## 4. Duplicate Protection at Both Layers

| Layer | Mechanism | Behavior |
| :--- | :--- | :--- |
| **Android Local DB** | SQLite Unique Index on `sms_hash` column | If the same SMS arrives multiple times, Room ignores the duplicate insert (`OnConflictStrategy.IGNORE`). |
| **Backend API** | Query on `user_id`, `source_type="sms"`, and `source_reference=sms_hash` | If an identical hash is submitted, backend returns `HTTP 409 Conflict`. Android treats 409 as successfully synced to avoid perpetual retry loops. |

---

## 5. Offline Queue & Network Recovery

1. When an SMS arrives while the device has cellular signal but **no internet connectivity**, `SmsReceiver` stores the transaction in the Room database with status `PENDING`.
2. WorkManager registers a one-time job (`SyncWorker`) constrained to `NetworkType.CONNECTED`.
3. As soon as Wi-Fi or mobile data connectivity is restored, the Android OS awakens `SyncWorker` in the background.
4. `SyncWorker` submits all queued transactions, marks them `SYNCED`, and records the sync timestamp.
5. If the server is unreachable, `SyncWorker` utilizes exponential backoff retry.

---

## 6. How to Build & Run the Android Client

### Prerequisites
- Java JDK 17 or higher
- Android Studio (Ladybug / Meerkat / Koala) or Android SDK Platform 34

### Opening in Android Studio
1. Open Android Studio.
2. Select **File -> Open...** and navigate to `d:\FinMate\android\FinMateSMS`.
3. Allow Gradle to sync dependencies.
4. Run on an Android emulator or connected physical device.

### Building via Command Line
```bash
cd android/FinMateSMS
# Run unit tests
./gradlew testDebugUnitTest

# Assemble Debug APK
./gradlew assembleDebug
```
The output APK will be generated at:
`android/FinMateSMS/app/build/outputs/apk/debug/app-debug.apk`

---

## 7. Configuration & Customization

### Configuring Allowed Bank Senders
1. Open the **FinMate SMS** app on your device.
2. Tap the **Settings** gear icon in the top right.
3. Edit the **Allowed Senders** comma-separated field:
   `HDFCBK, SBIINB, ICICIB, AXISBK, KOTAKB, PAYTM, CANBNK`
4. Tap **Save**.

### Configuring Server URL
- For Android Emulator: `http://10.0.2.2:8000`
- For Physical Device on Local Wi-Fi: `http://<your-computer-ip>:8000` (e.g. `http://192.168.1.50:8000`)

### Adding Support for New Bank Formats
To add custom parsing patterns for international or regional banks, update `SmsTransactionParser.kt`:
1. Add new keywords to `DEBIT_KEYWORDS` or `CREDIT_KEYWORDS`.
2. Add new amount regexes to `AMOUNT_PATTERNS`.
3. Add new date formats to `parseDateStringToIso()`.
4. Run `SmsTransactionParserTest.kt` to verify correctness.
