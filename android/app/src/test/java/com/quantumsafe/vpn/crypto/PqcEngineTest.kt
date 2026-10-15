package com.quantumsafe.vpn.crypto

import org.junit.Assert.*
import org.junit.Test

class PqcEngineTest {

    @Test
    fun testX25519KeyExchange() {
        val kp1 = PqcEngine.generateX25519KeyPair()
        val kp2 = PqcEngine.generateX25519KeyPair()

        assertEquals(PqcEngine.X25519_KEY_SIZE, kp1.publicKey.size)
        assertEquals(PqcEngine.X25519_KEY_SIZE, kp2.publicKey.size)

        val secret1 = PqcEngine.computeX25519SharedSecret(kp1.privateKey, kp2.publicKey)
        val secret2 = PqcEngine.computeX25519SharedSecret(kp2.privateKey, kp1.publicKey)

        assertArrayEquals(secret1, secret2)
        assertEquals(32, secret1.size)
    }

    @Test
    fun testKyberKeyExchange() {
        val kemKeys = PqcEngine.generateKemKeyPair()
        assertEquals(PqcEngine.MLKEM_PUBLIC_KEY_SIZE, kemKeys.publicKey.size)

        val kemGen = org.bouncycastle.pqc.crypto.crystals.kyber.KyberKEMGenerator(java.security.SecureRandom())
        val pubParams = org.bouncycastle.pqc.crypto.crystals.kyber.KyberPublicKeyParameters(
            org.bouncycastle.pqc.crypto.crystals.kyber.KyberParameters.kyber1024,
            kemKeys.publicKey
        )
        val enc = kemGen.generateEncapsulated(pubParams)
        val ciphertext = enc.encapsulation
        val senderSecret = enc.secret

        assertEquals(PqcEngine.MLKEM_CIPHERTEXT_SIZE, ciphertext.size)
        assertEquals(32, senderSecret.size)

        val receiverSecret = PqcEngine.decapsulateKem(kemKeys.secretKey, ciphertext)
        assertArrayEquals(senderSecret, receiverSecret)
    }

    @Test
    fun testDirectionalHkdfDerivation() {
        val sharedSecret = ByteArray(32) { 0x5A.toByte() }
        val transcript = "QuantumSafeVPN-v2-test-transcript".toByteArray(Charsets.UTF_8)

        val (kC2s, kS2c) = PqcEngine.deriveDirectionalKeys(sharedSecret, transcript)
        assertEquals(32, kC2s.size)
        assertEquals(32, kS2c.size)
        // Ensure k_c2s != k_s2c
        assertFalse(kC2s.contentEquals(kS2c))
    }

    @Test
    fun testAesGcmEncryptionDecryption() {
        val key = ByteArray(32) { 0x42.toByte() }
        val plaintext = "Hello QuantumSafe VPN Protocol v2!".toByteArray(Charsets.UTF_8)
        val seq = 99999L

        val encrypted = PqcEngine.encryptAesGcm(key, plaintext, seq)
        assertTrue(encrypted.size >= 12 + 8 + plaintext.size + 16)

        val (decSeq, decData) = PqcEngine.decryptAesGcm(key, encrypted)
        assertEquals(seq, decSeq)
        assertArrayEquals(plaintext, decData)
    }

    @Test(expected = Exception::class)
    fun testAesGcmTamperingRejection() {
        val key = ByteArray(32) { 0x42.toByte() }
        val plaintext = "Tamper check packet".toByteArray(Charsets.UTF_8)
        val encrypted = PqcEngine.encryptAesGcm(key, plaintext, 1L)

        val tampered = encrypted.copyOf()
        tampered[tampered.size - 2] = (tampered[tampered.size - 2].toInt() xor 0xFF).toByte()
        PqcEngine.decryptAesGcm(key, tampered)
    }

    @Test
    fun testShorDemonstrationWeakMode() {
        val res = PqcEngine.runShorDemonstration(isQuantumSafe = false)
        assertFalse(res.isQuantumSafe)
        assertTrue(res.success)
        assertEquals(16, res.modulusBitLength)
        assertTrue(res.statusMessage.contains("BROKEN"))
        assertTrue(res.decryptedPlaintext.contains("CONFIDENTIAL"))
    }

    @Test
    fun testShorDemonstrationQuantumSafeMode() {
        val res = PqcEngine.runShorDemonstration(isQuantumSafe = true)
        assertTrue(res.isQuantumSafe)
        assertFalse(res.success)
        assertEquals(1024, res.modulusBitLength)
        assertTrue(res.statusMessage.contains("QUANTUM-IMMUNE"))
        assertTrue(res.decryptedPlaintext.contains("PROTECTED"))
    }
}
