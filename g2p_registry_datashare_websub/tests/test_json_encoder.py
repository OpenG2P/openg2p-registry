import base64
from datetime import date, datetime, timezone

from odoo.tests import TransactionCase, tagged

from ..json_encoder import WebSubJSONEncoder


@tagged("post_install", "-at_install")
class TestWebSubJSONEncoder(TransactionCase):
    def test_bytes_encoding(self):
        # Test encoding of bytes to base64 string
        encoder = WebSubJSONEncoder()
        test_bytes = b"test bytes"
        expected_output = base64.b64encode(test_bytes).decode()
        self.assertEqual(encoder.default(test_bytes), expected_output)

    def test_datetime_encoding(self):
        # Test encoding of datetime to ISO 8601 format with milliseconds and 'Z' suffix
        encoder = WebSubJSONEncoder()
        test_datetime = datetime(2023, 10, 1, 12, 30, 45, tzinfo=timezone.utc)
        expected_output = "2023-10-01T12:30:45.000Z"
        self.assertEqual(encoder.default(test_datetime), expected_output)

    def test_date_encoding(self):
        # Test encoding of date to ISO 8601 format
        encoder = WebSubJSONEncoder()
        test_date = date(2023, 10, 1)
        expected_output = "2023-10-01"
        self.assertEqual(encoder.default(test_date), expected_output)

    def test_python_dict_to_json_dict(self):
        # Test conversion of a Python dictionary to a JSON-compatible dictionary
        test_dict = {
            "bytes": b"test bytes",
            "datetime": datetime(2023, 10, 1, 12, 30, 45, tzinfo=timezone.utc),
            "date": date(2023, 10, 1),
        }
        expected_output = {
            "bytes": base64.b64encode(b"test bytes").decode(),
            "datetime": "2023-10-01T12:30:45.000Z",
            "date": "2023-10-01",
        }
        self.assertEqual(WebSubJSONEncoder.python_dict_to_json_dict(test_dict), expected_output)

    def test_default_behavior_for_unsupported_types(self):
        # Test fallback to default JSONEncoder behavior for unsupported types
        encoder = WebSubJSONEncoder()
        test_obj = {"key": "value"}
        with self.assertRaises(TypeError):
            encoder.default(test_obj)
