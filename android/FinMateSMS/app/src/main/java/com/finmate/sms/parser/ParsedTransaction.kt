package com.finmate.sms.parser

data class ParsedTransaction(
    val amount: Double,
    val transactionDate: String, // YYYY-MM-DD format
    val type: String, // "expense" or "income"
    val category: String = "Other",
    val description: String = "SMS Transaction",
    val source: String = "sms",
    val sender: String,
    val smsHash: String
)
