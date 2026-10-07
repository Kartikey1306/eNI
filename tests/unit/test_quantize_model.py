"""Unit tests for tools/quantize_model.py — the eNI INT8 quantization tool.

Covers quantize_weights / dequantize_weights (incl. edge cases) and the
write_eni_model binary format header. Part of the eNI#37 coverage drive.
"""

import struct
import unittest

from tools.quantize_model import (
    dequantize_weights,
    main,
    quantize_weights,
    read_eni_model,
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


class TestReadEniModel(unittest.TestCase):
    def _layers(self):
        return [
            {"name": "dense_0", "input_size": 4, "output_size": 2,
             "activation": 1, "weights": [0.1, 0.2, 0.3, 0.4,
                                          0.5, 0.6, 0.7, 0.8]},
        ]

    def test_roundtrip_float(self):
        import tempfile, os
        layers = self._layers()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "m.eni_model")
            write_eni_model(p, layers, quantized=False)
            back = read_eni_model(p)
        self.assertEqual(back["version"], 1)
        self.assertEqual(len(back["layers"]), 1)
        self.assertEqual(back["layers"][0]["name"], "dense_0")
        for w, b in zip(layers[0]["weights"], back["layers"][0]["weights"]):
            self.assertAlmostEqual(w, b, places=6)

    def test_rejects_bad_magic(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "bad.eni_model")
            with open(p, "wb") as f:
                f.write(b"\x00" * 64)
            with self.assertRaises(ValueError):
                read_eni_model(p)

    def test_rejects_truncated(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "short.eni_model")
            with open(p, "wb") as f:
                f.write(struct.pack("<II", 0x454E4931, 1))
            with self.assertRaises(ValueError):
                read_eni_model(p)


class TestMainFailClosed(unittest.TestCase):
    """eNI#40: the tool must quantize its input or refuse — never emit a
    placeholder while reporting success. All offline, fixture-based."""

    def _write_float_model(self, path, weights):
        write_eni_model(path, [{"name": "dense_0", "input_size": 4,
                                "output_size": 2, "activation": 1,
                                "weights": weights}], quantized=False)

    def test_refuses_missing_input(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "o.q")
            with self.assertRaises(SystemExit) as cm:
                main(["-i", os.path.join(d, "nope.eni_model"), "-o", out])
            self.assertNotEqual(cm.exception.code, 0)
            self.assertFalse(os.path.exists(out))

    def test_refuses_zero_weight_model(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            inp = os.path.join(d, "z.eni_model")
            out = os.path.join(d, "o.q")
            self._write_float_model(inp, [0.0] * 8)
            with self.assertRaises(SystemExit) as cm:
                main(["-i", inp, "-o", out])
            self.assertNotEqual(cm.exception.code, 0)
            self.assertFalse(os.path.exists(out))

    def test_refuses_onnx_without_runtime_quantizer(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            inp = os.path.join(d, "m.onnx")
            out = os.path.join(d, "o.q")
            with open(inp, "wb") as f:
                f.write(b"not a real onnx file")
            with self.assertRaises(SystemExit) as cm:
                main(["-i", inp, "-o", out])
            self.assertNotEqual(cm.exception.code, 0)
            self.assertFalse(os.path.exists(out))

    def test_refuses_corrupt_model(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            inp = os.path.join(d, "bad.eni_model")
            out = os.path.join(d, "o.q")
            with open(inp, "wb") as f:
                f.write(b"\x01\x02\x03")
            with self.assertRaises(SystemExit) as cm:
                main(["-i", inp, "-o", out])
            self.assertNotEqual(cm.exception.code, 0)
            self.assertFalse(os.path.exists(out))

    def test_quantizes_real_input(self):
        import tempfile, os
        weights = [0.1, -0.5, 0.9, -0.05, 0.33, 1.5, -1.2, 0.01]
        with tempfile.TemporaryDirectory() as d:
            inp = os.path.join(d, "m.eni_model")
            out = os.path.join(d, "m.q")
            self._write_float_model(inp, weights)
            main(["-i", inp, "-o", out])  # must not raise
            self.assertTrue(os.path.exists(out))
            back = read_eni_model(out)
            self.assertEqual(back["version"], 2)
            layer = back["layers"][0]
            # output actually encodes the input: not placeholder-shaped
            self.assertTrue(any(w != 0 for w in layer["weights"]))
            deq = dequantize_weights(layer["weights"], layer["scale"],
                                     layer["zero_point"])
            for w, b in zip(weights, deq):
                self.assertLess(abs(w - b), layer["scale"])

    def test_info_does_not_write_output(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            inp = os.path.join(d, "m.eni_model")
            out = os.path.join(d, "o.q")
            self._write_float_model(inp, [0.5] * 8)
            main(["-i", inp, "-o", out, "--info"])  # must not raise
            self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
