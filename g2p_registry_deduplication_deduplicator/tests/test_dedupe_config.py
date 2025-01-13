from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, mute_logger, tagged


@tagged("post_install", "-at_install")
class TestG2PDeduplication(TransactionCase):
    def setUp(self):
        # Set up test data
        super().setUp()
        self.dedupe_config = self.env["g2p.registry.deduplication.deduplicator.config"].create(
            {
                "name": "Test Config",
                "config_name": "test_config",
                "dedupe_service_base_url": "http://test-service",
                "dedupe_service_api_timeout": 5,
                "config_index_name": "test_index",
                "config_score_threshold": 0.8,
                "active": True,
            }
        )

        self.config_field = self.env["g2p.registry.deduplication.deduplicator.config.field"].create(
            {
                "name": "test_field",
                "fuzziness": "AUTO",
                "weightage": 1.0,
                "exact": False,
                "dedupe_config_id": self.dedupe_config.id,
            }
        )

        self.test_partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

    @patch("requests.put")
    @mute_logger("odoo.addons.g2p_registry_deduplication_deduplicator.models.dedupe_config")
    def test_save_upload_config_success(self, mock_put):
        # Test successful config upload
        mock_put.return_value.ok = True
        mock_put.return_value.raise_for_status.return_value = None

        self.dedupe_config.save_upload_config()

        mock_put.assert_called_once()
        called_url = mock_put.call_args[0][0]
        self.assertEqual(called_url, "http://test-service/config/test_config")

    @patch("requests.put")
    @mute_logger("odoo.addons.g2p_registry_deduplication_deduplicator.models.dedupe_config")
    def test_save_upload_config_failure(self, mock_put):
        # Test failed config upload
        mock_put.return_value.ok = False
        mock_put.return_value.raise_for_status.side_effect = Exception("API Error")

        with self.assertRaises(ValidationError):
            self.dedupe_config.save_upload_config()

    def test_get_configured_deduplicator(self):  # Test retrieving configured deduplicator
        self.env["ir.config_parameter"].sudo().set_param(
            "g2p_registry_deduplication_deduplicator.deduplicator_config_id", str(self.dedupe_config.id)
        )

        result = self.dedupe_config.get_configured_deduplicator()
        self.assertEqual(result, self.dedupe_config)

    @patch("requests.get")
    @mute_logger("odoo.addons.g2p_registry_deduplication_deduplicator.models.dedupe_config")
    def test_get_duplicates_by_record_id_success(self, mock_get):
        # Test successful duplicate retrieval
        mock_response = {"duplicates": [{"id": self.test_partner.id, "score": 0.95}]}
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status.return_value = None

        duplicates = self.dedupe_config.get_duplicates_by_record_id(self.test_partner.id)

        self.assertEqual(len(duplicates), 1)
        self.assertEqual(duplicates[0]["id"], self.test_partner.id)
        self.assertEqual(duplicates[0]["name"], self.test_partner.name)

    @patch("requests.get")
    @mute_logger("odoo.addons.g2p_registry_deduplication_deduplicator.models.dedupe_config")
    def test_get_duplicates_by_record_id_failure(self, mock_get):
        # Test failed duplicate retrieval
        mock_get.return_value.ok = False
        mock_get.return_value.raise_for_status.side_effect = Exception("API Error")

        with self.assertRaises(ValidationError):
            self.dedupe_config.get_duplicates_by_record_id(self.test_partner.id)
