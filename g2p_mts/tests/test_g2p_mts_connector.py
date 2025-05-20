from datetime import date
from unittest.mock import patch

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestG2PMTSConnector(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, test_queue_job_no_delay=True))

        cls.vid_type = cls.env["g2p.id.type"].create({"name": "MOSIP VID"})
        cls.uin_type = cls.env["g2p.id.type"].create({"name": "MOSIP UIN TOKEN"})

        cls.env["ir.config_parameter"].sudo().set_param("g2p_mts.vid_id_type", cls.vid_type.id)
        cls.env["ir.config_parameter"].sudo().set_param("g2p_mts.uin_token_id_type", cls.uin_type.id)

        cls.connector = cls.env["mts.connector"].create(
            {
                "name": "Test G2P Connector",
                "mts_url": "http://test-mts.local",
                "input_type": "custom",
                "output_type": "json",
                "delivery_type": "callback",
                "callback_url": "http://callback.local",
                "callback_httpmethod": "POST",
                "callback_timeout": 10,
                "is_recurring": "onetime",
            }
        )

        cls.registrant = cls.env["res.partner"].create(
            {
                "name": "Test Registrant",
                "is_registrant": True,
                "reg_ids": [(0, 0, {"id_type": cls.vid_type.id, "value": "123456789"})],
            }
        )

    def test_json_field_constraints(self):
        # Test constrains_g2p_mts_json_fields
        with self.assertRaises(ValidationError):
            self.connector.write({"g2p_search_domain": "invalid json"})

        with self.assertRaises(ValidationError):
            self.connector.write({"g2p_selected_fields": "invalid json"})

        self.connector.write(
            {"g2p_search_domain": '[["is_registrant", "=", true]]', "g2p_selected_fields": '["name", "id"]'}
        )

    @patch("odoo.addons.g2p_mts.models.g2p_mts_connector.requests.post")
    def test_custom_single_action(self, mock_post):
        # Test custom_single_action method
        mock_post.return_value.text = "success"

        mts_request = {"request": {}}

        self.connector.custom_single_action(mts_request)

        self.assertTrue(mock_post.called)
        call_args = mock_post.call_args
        self.assertIn("authdata", call_args[1]["json"]["request"])

        self.assertEqual(self.connector.job_status, "completed")

    def test_delete_vids_if_token(self):
        # Test video deletion when UIN token exists
        self.registrant.write({"reg_ids": [(0, 0, {"id_type": self.uin_type.id, "value": "UIN123456"})]})

        self.env["ir.config_parameter"].sudo().set_param(
            "g2p_mts.vid_delete_search_domain", '[["is_registrant", "=", true]]'
        )

        initial_reg_ids_count = len(self.registrant.reg_ids)
        self.connector.delete_vids_if_token()

        self.assertEqual(
            len(self.registrant.reg_ids),
            initial_reg_ids_count - 1,
            "VID should be deleted when UIN token exists",
        )

    def test_read_record_list(self):
        # Test reading record list from record set
        record_set = self.env["res.partner"].search([("id", "=", self.registrant.id)])
        field_list = ["name", "id"]

        result = self.connector.read_record_list_from_rec_set(record_set, field_list)

        self.assertEqual(len(result), 1)
        self.assertIn("name", result[0])
        self.assertIn("id", result[0])
        self.assertEqual(result[0]["name"], self.registrant.name)

    def test_record_set_json_serialize(self):
        # Test record_set_json_serialize with datetime object
        test_date = date(2024, 1, 1)
        serialized_date = self.connector.record_set_json_serialize(test_date)
        self.assertEqual(serialized_date, "2024/01/01")

        test_obj = object()
        serialized_obj = self.connector.record_set_json_serialize(test_obj)
        self.assertEqual(serialized_obj, str(test_obj))
