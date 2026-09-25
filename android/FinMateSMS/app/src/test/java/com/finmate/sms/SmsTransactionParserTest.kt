package com.finmate.sms

import com.finmate.sms.parser.SmsTransactionParser
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class SmsTransactionParserTest {

    @Test
    fun testHdfcDebitSmsParsing() {
        val message = "Rs.850.00 debited from A/c XX1234 on 25-09-2026. Info: Swiggy. Bal: Rs.14,250.00"
        val parsed = SmsTransactionParser.parse(
            sender = "HDFCBK",
            messageBody = message,
            receivedTimestamp = 1790320000000L
        )

        assertNotNull(parsed)
        assertEquals(850.0, parsed!!.amount, 0.001)
        assertEquals("2026-09-25", parsed.transactionDate)
        assertEquals("expense", parsed.type)
        assertEquals("Other", parsed.category)
        assertEquals("SMS Transaction", parsed.description)
        assertEquals("sms", parsed.source)
        assertEquals("HDFCBK", parsed.sender)
        assertNotNull(parsed.smsHash)
    }

    @Test
    fun testSbiCreditSmsParsing() {
        val message = "Dear Customer, A/c *8901 credited by Rs 45,000.00 on 25-09-2026 by transfer from Employer Ltd."
        val parsed = SmsTransactionParser.parse(
            sender = "SBIINB",
            messageBody = message
        )

        assertNotNull(parsed)
        assertEquals(45000.0, parsed!!.amount, 0.001)
        assertEquals("2026-09-25", parsed.transactionDate)
        assertEquals("income", parsed.type)
        assertEquals("Other", parsed.category)
        assertEquals("SMS Transaction", parsed.description)
        assertEquals("SBIINB", parsed.sender)
    }

    @Test
    fun testIciciDebitWithCurrencySymbol() {
        val message = "Your A/C XX5678 has been debited for ₹1,250.50 on 25/09/2026. Avl Bal: ₹23,100"
        val parsed = SmsTransactionParser.parse(
            sender = "ICICIB",
            messageBody = message
        )

        assertNotNull(parsed)
        assertEquals(1250.50, parsed!!.amount, 0.001)
        assertEquals("2026-09-25", parsed.transactionDate)
        assertEquals("expense", parsed.type)
    }

    @Test
    fun testInrKeywordAndTextDate() {
        val message = "INR 3,500.00 spent on your Axis Card XX9900 on 25 Sep 2026 at Croma."
        val parsed = SmsTransactionParser.parse(
            sender = "AXISBK",
            messageBody = message
        )

        assertNotNull(parsed)
        assertEquals(3500.0, parsed!!.amount, 0.001)
        assertEquals("2026-09-25", parsed.transactionDate)
        assertEquals("expense", parsed.type)
    }

    @Test
    fun testOtpMessageRejectedForPrivacy() {
        val otpMessage = "123456 is your secret OTP for transaction of Rs. 850.00 at Swiggy. Do not share this with anyone."
        val parsed = SmsTransactionParser.parse(
            sender = "HDFCBK",
            messageBody = otpMessage
        )

        // Must reject OTP messages to protect privacy and security
        assertNull("OTP message must not be parsed as a transaction", parsed)
    }

    @Test
    fun testPromotionalNonFinancialMessageRejected() {
        val promoMessage = "Get pre-approved personal loan up to Rs. 5,00,000 at 10.5% interest. Apply now!"
        val parsed = SmsTransactionParser.parse(
            sender = "HDFCBK",
            messageBody = promoMessage
        )

        assertNull("Promotional message must be rejected", parsed)
    }

    @Test
    fun testDeterministicHashConsistency() {
        val message = "Rs.850 debited from A/c XX1234 on 25-09-2026"
        val parsed1 = SmsTransactionParser.parse("HDFCBK", message, 1000000L)
        val parsed2 = SmsTransactionParser.parse("HDFCBK", message, 1000000L)

        assertNotNull(parsed1)
        assertNotNull(parsed2)
        assertEquals(parsed1!!.smsHash, parsed2!!.smsHash)
    }
}
