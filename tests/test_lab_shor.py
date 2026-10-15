"""
Tests for the isolated Shor lab.  Run:  python -m unittest tests.test_lab_shor -v
"""
import os
import random
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lab import shor_demo as lab  # noqa: E402


class ShorLabTests(unittest.TestCase):
    def test_emulated_quantum_step_matches_exact_statevector(self):
        """Emulator output distribution must match an exact FFT simulation (N=21, a=2, r=6)."""
        n, a, t = 21, 2, 10
        exact = lab.exact_order_distribution(a, n, t)
        self.assertAlmostEqual(exact.sum(), 1.0, places=6)
        rng = random.Random(1234)
        counts = np.zeros(1 << t)
        trials = 20000
        for _ in range(trials):
            k, q = lab.emulate_quantum_order_finding(a, n, rng, counting_bits=t)
            counts[k] += 1
        tv = 0.5 * np.abs(counts / trials - exact).sum()
        self.assertLess(tv, 0.08, f"total-variation distance too large: {tv:.4f}")

    def test_exact_simulation_peaks_at_multiples_of_q_over_r(self):
        n, a, t = 15, 7, 8  # r = 4
        exact = lab.exact_order_distribution(a, n, t)
        top = sorted(np.argsort(exact)[-4:])
        self.assertEqual(top, [0, 64, 128, 192])

    def test_recover_order(self):
        # N=15, a=7, r=4, Q=256: peak k=64 -> 64/256 = 1/4
        self.assertEqual(lab.recover_order(64, 256, 7, 15), 4)

    def test_shor_factors_every_valid_16bit_modulus_sample(self):
        rng = random.Random(7)
        for _ in range(25):
            rsa = lab.generate_rsa16(rng)
            self.assertTrue(32768 <= rsa["n"] < 65536)
            p, q, _ = lab.shor_factor(rsa["n"], rng, log=lambda s: None)
            self.assertEqual(sorted((p, q)), sorted((rsa["p"], rsa["q"])))

    def test_standard_mode_is_broken_and_plaintext_recovered(self):
        out = lab.run_standard(random.Random(42), log=lambda s: None)
        self.assertTrue(out["broken"])
        self.assertTrue(out["recovered_key_ok"])
        self.assertEqual(out["plaintext"], lab.SYNTHETIC_TRAFFIC)

    def test_quantum_safe_mode_resists_same_attacker(self):
        out = lab.run_quantum_safe(random.Random(42), log=lambda s: None, guesses=2000)
        self.assertFalse(out["broken"])
        self.assertTrue(out["legit_ok"], "legitimate endpoint must still decrypt")

    def test_wrong_key_cannot_decrypt(self):
        key = bytes(range(16))
        frames = lab._aes_traffic(key, lab.SYNTHETIC_TRAFFIC)
        self.assertIsNone(lab._try_decrypt(bytes(16), frames))
        self.assertEqual(lab._try_decrypt(key, frames), lab.SYNTHETIC_TRAFFIC)


if __name__ == "__main__":
    unittest.main(verbosity=2)
