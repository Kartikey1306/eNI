"""Unit tests for eni/geolocation/ip_geolocator.py — the IP-based location fallback.

Offline: urllib.request.urlopen is mocked, so both paths (the API answers,
the API is unreachable) run deterministically in CI instead of depending on
whether ipapi.co is reachable from the runner. Part of the eNI#37 coverage
drive.
"""

import json
import unittest
import urllib.error
from unittest import mock

from eni.geolocation.ip_geolocator import IPGeolocator


def _response(payload):
    resp = mock.MagicMock()
    resp.read.return_value = json.dumps(payload).encode()
    resp.__enter__.return_value = resp
    return resp


class TestIPGeolocatorSuccess(unittest.TestCase):
    def test_api_fields_are_mapped(self):
        payload = {"latitude": 48.85, "longitude": 2.35, "city": "Paris", "country_name": "France"}
        with mock.patch("urllib.request.urlopen", return_value=_response(payload)) as urlopen:
            res = IPGeolocator().get_location_by_ip()
        self.assertEqual(
            res,
            {"latitude": 48.85, "longitude": 2.35, "city": "Paris", "country": "France", "status": "success"},
        )
        req = urlopen.call_args.args[0]
        self.assertEqual(req.full_url, "https://ipapi.co/json/")
        self.assertEqual(req.get_header("User-agent"), "eNI-Network-Stack/1.0")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 5)

    def test_missing_fields_take_the_documented_defaults(self):
        with mock.patch("urllib.request.urlopen", return_value=_response({})):
            res = IPGeolocator().get_location_by_ip()
        self.assertEqual(res["status"], "success")
        self.assertEqual((res["latitude"], res["longitude"]), (37.7749, -122.4194))
        self.assertEqual((res["city"], res["country"]), ("San Francisco", "United States"))


class TestIPGeolocatorFallback(unittest.TestCase):
    def test_unreachable_api_returns_a_labelled_fallback(self):
        err = urllib.error.URLError("no route to host")
        with mock.patch("urllib.request.urlopen", side_effect=err):
            res = IPGeolocator().get_location_by_ip()
        self.assertEqual(res["status"], "fallback")
        self.assertIn("no route to host", res["error"])
        self.assertEqual((res["latitude"], res["longitude"]), (37.7749, -122.4194))

    def test_malformed_response_returns_a_labelled_fallback(self):
        resp = mock.MagicMock()
        resp.read.return_value = b"not json"
        resp.__enter__.return_value = resp
        with mock.patch("urllib.request.urlopen", return_value=resp):
            res = IPGeolocator().get_location_by_ip()
        self.assertEqual(res["status"], "fallback")
        self.assertTrue(res["error"])

    def test_coordinates_are_in_range_on_both_paths(self):
        cases = [
            mock.patch("urllib.request.urlopen", return_value=_response({"latitude": -33.9, "longitude": 151.2})),
            mock.patch("urllib.request.urlopen", side_effect=OSError("down")),
        ]
        for patcher in cases:
            with patcher:
                res = IPGeolocator().get_location_by_ip()
            self.assertTrue(-90.0 <= res["latitude"] <= 90.0)
            self.assertTrue(-180.0 <= res["longitude"] <= 180.0)
            self.assertIsInstance(res["city"], str)
            self.assertTrue(res["city"])


if __name__ == "__main__":
    unittest.main()
