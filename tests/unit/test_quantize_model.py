"""Unit tests for tools/quantize_model.py — the eNI INT8 quantization tool.

Covers quantize_weights / dequantize_weights (incl. edge cases) and the
write_eni_model binary format header. Part of the eNI#37 coverage drive.
"""

import struct
import unittest

from tools.quantize_model import (
    dequantize_weights,
    quantize_weights,
    write_eni_model,
)


class TestQuantizeWeights(unittest.TestCase):
    def test_empty_returns_empty(self):
        q, scale, zp = quantize_weights([])
        self.assertEqual(q, [])
        self.assertEqual(scale, 1.0)
        self.assertEqual(zp, 0)

    def test_all_zeros(self):
        q, scale, zp = quantize_weights([0.0, 0.0, 0.0])
        self.assertEqual(q, [0, 0, 0])
        self.assertEqual(scale, 1.0)

    def test_symmetric_range(self):
        q, scale, zp = quantize_weights([-1.0, 0.0, 1.0], bits=8)
        self.assertEqual(q, [-127, 0, 127])
        self.assertAlmostEqual(scale, 1.0 / 127)

    def test_clamps_outliers(self):
        # one large value sets the scale; the rest must clamp, not overflow
        q, scale, _ = quantize_weights([0.5, 100.0], bits=8)
        self.assertEqual(q[1], 127)
        self.assertTrue(all(-127 <= v <= 127 for v in q))

    def test_4bit(self):
        q, scale, _ = quantize_weights([-1.0, 1.0], bits=4)
        self.assertEqual(q, [-7, 7])

    def test_roundtrip_error_bounded(self):
        weights = [0.1, -0.5, 0.9, -0.05, 0.33]
        q, scale, zp = quantize_weights(weights, bits=8)
        back = dequantize_weights(q, scale, zp)
        for w, b in zip(weights, back):
            self.assertLess(abs(w - b), scale)

    def test_dequantize_with_zero_point(self):
        self.assertEqual(dequantize_weights([10, 20], 0.5, zero_point=10),
                         [0.0, 5.0])


class TestWriteEniModel(unittest.TestCase):
    def _layers(self):
        return [
            {"name": "dense_0", "input_size": 4, "output_size": 2,
             "activation": 1, "weights": [0.1, 0.2, 0.3, 0.4,
                                          0.5, 0.6, 0.7, 0.8]},
        ]

    def test_float_model_header(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.eni")
            write_eni_model(p, self._layers(), quantized=False)
            with open(p, "rb") as f:
                magic, version, n_layers = struct.unpack("<III", f.read(12))
        self.assertEqual(magic, 0x454E4931)
        self.assertEqual(version, 1)
        self.assertEqual(n_layers, 1)

    def test_quantized_model_header(self):
        import tempfile, os
        layers = self._layers()
        layers[0]["weights"], layers[0]["scale"], layers[0]["zero_point"] = \
            quantize_weights(layers[0]["weights"], bits=8)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.eni")
            write_eni_model(p, layers, quantized=True)
            with open(p, "rb") as f:
                magic, version, n_layers = struct.unpack("<III", f.read(12))
        self.assertEqual(magic, 0x454E4931)
        self.assertEqual(version, 2)
        self.assertEqual(n_layers, 1)

    def test_quantized_weights_roundtrip(self):
        import tempfile, os
        layers = self._layers()
        orig = list(layers[0]["weights"])
        layers[0]["weights"], layers[0]["scale"], layers[0]["zero_point"] = \
            quantize_weights(orig, bits=8)
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.eni")
            write_eni_model(p, layers, quantized=True)
            with open(p, "rb") as f:
                data = f.read()
        # header(12) + name(32) + in/out(8) + act(4) + scale(4) + zp(4) = 64
        body = data[64:]
        self.assertEqual(len(body), 8)  # 8 int8 weights
        back = dequantize_weights(list(struct.unpack("<8b", body)),
                                  layers[0]["scale"], layers[0]["zero_point"])
        for w, b in zip(orig, back):
            self.assertLess(abs(w - b), layers[0]["scale"] * 2)


if __name__ == "__main__":
    unittest.main()
