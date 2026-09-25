package com.finmate.sms.parser

import java.security.MessageDigest
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.regex.Pattern

object SmsTransactionParser {

    private val AMOUNT_PATTERNS = listOf(
        Pattern.compile("""(?i)(?:rs\.?|inr|₹)\s*([\d,]+(?:\.\d{1,2})?)"""),
        Pattern.compile("""(?i)([\d,]+(?:\.\d{1,2})?)\s*(?:rs\.?|inr|₹)"""),
        Pattern.compile("""(?i)(?:debited\s+by|credited\s+by|amount\s+of)\s*([\d,]+(?:\.\d{1,2})?)""")
    )

    private val DEBIT_KEYWORDS = listOf(
        "debited", "debit", "spent", "paid", "withdrawn",
        "transferred", "sent", "purchase", "dr"
    )

    private val CREDIT_KEYWORDS = listOf(
        "credited", "credit", "received", "deposited",
        "refunded", "reversal", "cr"
    )

    private val OTP_PATTERNS = listOf(
        Pattern.compile("""(?i)\b(otp|one\s*time\s*password|verification\s*code|secret\s*code)\b"""),
        Pattern.compile("""(?i)\bdo\s*not\s*share\b""")
    )

    private val DATE_PATTERNS = listOf(
        Pattern.compile("""\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})\b"""),
        Pattern.compile("""\b(\d{1,2})[-/\s]([A-Za-z]{3,9})[-/\s](\d{2,4})\b""")
    )

    /**
     * Parses an incoming SMS message. Returns ParsedTransaction if valid financial transaction,
     * or null if parsing fails or message is non-financial (e.g. OTP, marketing).
     */
    fun parse(sender: String, messageBody: String, receivedTimestamp: Long = System.currentTimeMillis()): ParsedTransaction? {
        if (messageBody.isBlank()) return null

        // 1. Guard: Check for OTP or authentication tokens (Privacy & Safety)
        if (isOtpOrAuthMessage(messageBody)) {
            return null
        }

        // 2. Extract Transaction Type (Debit vs Credit)
        val transactionType = determineTransactionType(messageBody) ?: return null

        // 3. Extract Amount
        val amount = extractAmount(messageBody) ?: return null
        if (amount <= 0.0) return null

        // 4. Extract Date (with fallback to received timestamp)
        val dateString = extractDate(messageBody, receivedTimestamp)

        // 5. Generate deterministic SHA-256 hash for duplicate protection
        val smsHash = generateSmsHash(sender, dateString, amount, transactionType, messageBody)

        return ParsedTransaction(
            amount = amount,
            transactionDate = dateString,
            type = transactionType,
            category = "Other",
            description = "SMS Transaction",
            source = "sms",
            sender = sender.trim().uppercase(),
            smsHash = smsHash
        )
    }

    private fun isOtpOrAuthMessage(body: String): Boolean {
        for (pattern in OTP_PATTERNS) {
            if (pattern.matcher(body).find()) {
                return true
            }
        }
        return false
    }

    private fun determineTransactionType(body: String): String? {
        val lower = body.lowercase(Locale.ENGLISH)

        // Count occurrences of debit vs credit signals
        val isDebit = DEBIT_KEYWORDS.any { Regex("""\b$it\b""").containsMatchIn(lower) }
        val isCredit = CREDIT_KEYWORDS.any { Regex("""\b$it\b""").containsMatchIn(lower) }

        return when {
            isDebit && !isCredit -> "expense"
            isCredit && !isDebit -> "income"
            isDebit && isCredit -> {
                // If both present, prioritize explicit phrasing: "debited from" -> expense, "credited to" -> income
                if (lower.contains("debited from") || lower.contains("spent on") || lower.contains("paid to")) {
                    "expense"
                } else if (lower.contains("credited to") || lower.contains("deposited in") || lower.contains("refund of")) {
                    "income"
                } else {
                    "expense"
                }
            }
            else -> null
        }
    }

    private fun extractAmount(body: String): Double? {
        for (pattern in AMOUNT_PATTERNS) {
            val matcher = pattern.matcher(body)
            if (matcher.find()) {
                val rawNumber = matcher.group(1)?.replace(",", "") ?: continue
                try {
                    val parsed = rawNumber.toDouble()
                    if (parsed > 0) return parsed
                } catch (_: NumberFormatException) {
                    continue
                }
            }
        }
        return null
    }

    private fun extractDate(body: String, fallbackTimestamp: Long): String {
        for (pattern in DATE_PATTERNS) {
            val matcher = pattern.matcher(body)
            if (matcher.find()) {
                val matchStr = matcher.group(0) ?: continue
                val parsedDate = parseDateStringToIso(matchStr)
                if (parsedDate != null) {
                    return parsedDate
                }
            }
        }

        // Fallback: format SMS received timestamp safely into YYYY-MM-DD
        val sdf = SimpleDateFormat("yyyy-MM-dd", Locale.US)
        return sdf.format(Date(fallbackTimestamp))
    }

    private fun parseDateStringToIso(rawDate: String): String? {
        val formats = listOf(
            "dd-MM-yyyy", "dd/MM/yyyy", "dd.MM.yyyy",
            "dd-MM-yy", "dd/MM/yy",
            "dd MMM yyyy", "dd-MMM-yyyy", "dd MMM yy", "dd-MMM-yy"
        )
        for (fmt in formats) {
            try {
                val sdf = SimpleDateFormat(fmt, Locale.US)
                sdf.isLenient = false
                val parsed = sdf.parse(rawDate.trim())
                if (parsed != null) {
                    val outSdf = SimpleDateFormat("yyyy-MM-dd", Locale.US)
                    return outSdf.format(parsed)
                }
            } catch (_: Exception) {
                continue
            }
        }
        return null
    }

    private fun generateSmsHash(
        sender: String,
        date: String,
        amount: Double,
        type: String,
        body: String
    ): String {
        // Normalize body: extract first 40 chars of alphanumeric content to avoid minor variations
        val cleanPreview = body.replace(Regex("""[^a-zA-Z0-9]"""), "").take(40).lowercase(Locale.ENGLISH)
        val rawKey = "${sender.trim().uppercase()}|$date|%.2f|$type|$cleanPreview".format(Locale.US, amount)

        val digest = MessageDigest.getInstance("SHA-256")
        val bytes = digest.digest(rawKey.toByteArray(Charsets.UTF_8))
        return bytes.joinToString("") { "%02x".format(it) }
    }
}
