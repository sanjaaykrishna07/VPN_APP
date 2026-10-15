package com.quantumsafe.vpn.crypto

import org.bouncycastle.crypto.agreement.X25519Agreement
import org.bouncycastle.crypto.generators.X25519KeyPairGenerator
import org.bouncycastle.crypto.params.X25519KeyGenerationParameters
import org.bouncycastle.crypto.params.X25519PrivateKeyParameters
import org.bouncycastle.crypto.params.X25519PublicKeyParameters
import org.bouncycastle.pqc.crypto.crystals.dilithium.DilithiumParameters
import org.bouncycastle.pqc.crypto.crystals.dilithium.DilithiumPublicKeyParameters
import org.bouncycastle.pqc.crypto.crystals.dilithium.DilithiumSigner
import org.bouncycastle.pqc.crypto.crystals.kyber.*
import org.junit.Assert.*
import org.junit.Test
import java.security.SecureRandom

class BouncyCastleTest {

    @Test
    fun testX25519KeyExchange() {
        val random = SecureRandom()
        val gen1 = X25519KeyPairGenerator().apply { init(X25519KeyGenerationParameters(random)) }
        val kp1 = gen1.generateKeyPair()
        val priv1 = kp1.private as X25519PrivateKeyParameters
        val pub1 = kp1.public as X25519PublicKeyParameters

        val gen2 = X25519KeyPairGenerator().apply { init(X25519KeyGenerationParameters(random)) }
        val kp2 = gen2.generateKeyPair()
        val priv2 = kp2.private as X25519PrivateKeyParameters
        val pub2 = kp2.public as X25519PublicKeyParameters

        val agree1 = X25519Agreement().apply { init(priv1) }
        val secret1 = ByteArray(32)
        agree1.calculateAgreement(pub2, secret1, 0)

        val agree2 = X25519Agreement().apply { init(priv2) }
        val secret2 = ByteArray(32)
        agree2.calculateAgreement(pub1, secret2, 0)

        assertArrayEquals(secret1, secret2)
        assertEquals(32, pub1.encoded.size)
    }

    @Test
    fun testKyber1024KeyExchange() {
        val random = SecureRandom()
        val keyGen = KyberKeyPairGenerator().apply {
            init(KyberKeyGenerationParameters(random, KyberParameters.kyber1024))
        }
        val keyPair = keyGen.generateKeyPair()
        val pub = keyPair.public as KyberPublicKeyParameters
        val priv = keyPair.private as KyberPrivateKeyParameters

        assertEquals(1568, pub.encoded.size)

        // Encapsulate
        val kemGen = KyberKEMGenerator(random)
        val secWithEnc = kemGen.generateEncapsulated(pub)
        val ciphertext = secWithEnc.encapsulation
        val secretSender = secWithEnc.secret

        assertEquals(1568, ciphertext.size)
        assertEquals(32, secretSender.size)

        // Decapsulate
        val extractor = KyberKEMExtractor(priv)
        val secretReceiver = extractor.extractSecret(ciphertext)

        assertArrayEquals(secretSender, secretReceiver)
    }

    @Test
    fun testDilithium3Verification() {
        // Dilithium3 corresponds to NIST Security Level 3 / ML-DSA-65 (1952 bytes public key)
        val d3Params = DilithiumParameters.dilithium3
        val dummyPk = ByteArray(1952)
        val pkParams = DilithiumPublicKeyParameters(d3Params, dummyPk)
        assertEquals(1952, pkParams.encoded.size)

        val signer = DilithiumSigner()
        signer.init(false, pkParams)
        // Dummy signature should fail verification gracefully without crash
        val dummySig = ByteArray(3309)
        val verified = signer.verifySignature("test message".toByteArray(), dummySig)
        assertFalse(verified)
    }
}
