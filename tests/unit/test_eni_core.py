"""Unit tests for the eNI Python bindings (eni/core.py).

Covers ENIProvider, DSPPipeline, NNModel, Decoder and FeedbackController —
the classes the Python test-suite exercises through the public API.
"""
import unittest

from eni.core import (
    Decoder,
    DSPPipeline,
    ENIError,
    ENIProvider,
    FeedbackController,
    NNModel,
)


class TestENIError(unittest.TestCase):
    def test_is_exception(self):
        with self.assertRaises(ENIError):
            raise ENIError("boom")

    def test_message_preserved(self):
        try:
            raise ENIError("neural link lost")
        except ENIError as e:
            self.assertEqual(str(e), "neural link lost")


class TestENIProvider(unittest.TestCase):
    def test_default_is_simulator(self):
        p = ENIProvider()
        self.assertEqual(p._provider_type, "simulator")

    def test_custom_provider_type(self):
        p = ENIProvider(provider_type="hardware")
        self.assertEqual(p._provider_type, "hardware")

    def test_connect_disconnect(self):
        p = ENIProvider()
        self.assertFalse(p._connected)
        p.connect()
        self.assertTrue(p._connected)
        p.disconnect()
        self.assertFalse(p._connected)

    def test_context_manager_connects_and_disconnects(self):
        with ENIProvider() as p:
            self.assertTrue(p._connected)
        self.assertFalse(p._connected)

    def test_context_manager_returns_self(self):
        p = ENIProvider()
        with p as ctx:
            self.assertIs(ctx, p)


class TestDSPPipeline(unittest.TestCase):
    def test_defaults(self):
        d = DSPPipeline()
        self.assertEqual(d.sample_rate, 256)
        self.assertEqual(d.fft_size, 256)
        self.assertEqual(d.channels, 64)

    def test_fft_size_clamped_to_max(self):
        d = DSPPipeline(fft_size=2048)
        self.assertEqual(d.fft_size, DSPPipeline.MAX_FFT_SIZE)

    def test_fft_size_below_max_kept(self):
        d = DSPPipeline(fft_size=128)
        self.assertEqual(d.fft_size, 128)

    def test_process_requires_init(self):
        d = DSPPipeline()
        with self.assertRaises(ENIError):
            d.process([0.1, 0.2])

    def test_process_returns_power_spectrum(self):
        d = DSPPipeline()
        d.init()
        out = d.process([1.0, -2.0, 0.5])
        self.assertEqual(out, [1.0, 4.0, 0.25])

    def test_process_empty(self):
        d = DSPPipeline()
        d.init()
        self.assertEqual(d.process([]), [])


class TestNNModel(unittest.TestCase):
    def test_predict_requires_load(self):
        m = NNModel()
        with self.assertRaises(ENIError):
            m.predict([0.1])

    def test_predict_after_load(self):
        m = NNModel()
        m.load("model.bin")
        r = m.predict([0.2, 0.4])
        self.assertEqual(r["intent"], "idle")
        self.assertGreaterEqual(r["confidence"], 0.0)
        self.assertLessEqual(r["confidence"], 1.0)

    def test_predict_confidence_clamped(self):
        m = NNModel()
        m.load("model.bin")
        r = m.predict([100.0, 100.0])
        self.assertLessEqual(r["confidence"], 1.0)

    def test_predict_empty_features(self):
        m = NNModel()
        m.load("model.bin")
        r = m.predict([])
        self.assertEqual(r["confidence"], 0.0)


class TestDecoder(unittest.TestCase):
    def test_intent_vocabulary(self):
        for intent in ("idle", "left", "right", "up", "down", "select", "back"):
            self.assertIn(intent, Decoder.INTENTS)

    def test_decode_returns_known_intent(self):
        d = Decoder()
        r = d.decode([0.1, 0.2, 0.3])
        self.assertIn(r["intent"], Decoder.INTENTS)
        self.assertGreaterEqual(r["confidence"], 0.0)
        self.assertLessEqual(r["confidence"], 1.0)

    def test_decode_is_deterministic(self):
        d = Decoder()
        self.assertEqual(d.decode([0.5]), d.decode([0.5]))

    def test_decode_empty_features(self):
        d = Decoder()
        r = d.decode([])
        self.assertEqual(r["intent"], "idle")


class TestFeedbackController(unittest.TestCase):
    def test_no_rules_matches_nothing(self):
        c = FeedbackController()
        self.assertIsNone(c.process({"intent": "left"}))

    def test_matching_rule_returns_command(self):
        c = FeedbackController()
        c.add_rule("left", "tms", 0.7)
        r = c.process({"intent": "left"})
        self.assertEqual(r, {"stim_type": "tms", "intensity": 0.7})

    def test_non_matching_intent_returns_none(self):
        c = FeedbackController()
        c.add_rule("left", "tms", 0.7)
        self.assertIsNone(c.process({"intent": "right"}))

    def test_missing_intent_key_returns_none(self):
        c = FeedbackController()
        c.add_rule("left", "tms", 0.7)
        self.assertIsNone(c.process({}))

    def test_first_matching_rule_wins(self):
        c = FeedbackController()
        c.add_rule("left", "tms", 0.5)
        c.add_rule("left", "tes", 0.9)
        r = c.process({"intent": "left"})
        self.assertEqual(r["stim_type"], "tms")


if __name__ == "__main__":
    unittest.main()
