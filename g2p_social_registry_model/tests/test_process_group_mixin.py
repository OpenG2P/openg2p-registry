from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProcessSocialGroupMixin(TransactionCase):
    def setUp(self):
        super().setUp()
        self.mixin = self.env["process_group.rest.mixin"]

    def _build_mock_group_info(self, fields):
        mock_info = MagicMock()
        mock_info.model_dump.return_value = fields
        return mock_info

    @patch(
        "odoo.addons.g2p_registry_rest_api.models.process_group_mixin.ProcessGroupMixin._process_group",
        return_value={"name": "Test Group"},
    )
    def test_process_group_with_social_and_economic_fields(self, mock_super):
        input_fields = {
            "num_preg_lact_women": 5,
            "num_malnourished_children": 3,
            "owns_two_wheeler": True,
            "annual_income": 50000,
        }

        mock_group_info = self._build_mock_group_info(input_fields)
        result = self.mixin._process_group(mock_group_info)

        for key in input_fields:
            self.assertIn(key, result)
            self.assertEqual(result[key], input_fields[key])

    @patch(
        "odoo.addons.g2p_registry_rest_api.models.process_group_mixin.ProcessGroupMixin._process_group",
        return_value={"name": "Test Group"},
    )
    def test_process_group_with_no_optional_fields(self, mock_super):
        mock_group_info = self._build_mock_group_info({})
        result = self.mixin._process_group(mock_group_info)
        self.assertEqual(result, {"name": "Test Group"})

    @patch(
        "odoo.addons.g2p_registry_rest_api.models.process_group_mixin.ProcessGroupMixin._process_group",
        return_value={"name": "Test Group"},
    )
    def test_process_group_with_partial_fields(self, mock_super):
        input_fields = {
            "caste_ethnic_group": "Scheduled Tribe",
            "land_ownership": True,
        }

        mock_group_info = self._build_mock_group_info(input_fields)
        result = self.mixin._process_group(mock_group_info)

        self.assertEqual(result["caste_ethnic_group"], "Scheduled Tribe")
        self.assertEqual(result["land_ownership"], True)

    @patch(
        "odoo.addons.g2p_registry_rest_api.models.process_group_mixin.ProcessGroupMixin._process_group",
        return_value={"name": "Test Group"},
    )
    def test_super_method_called_once(self, mock_super):
        mock_group_info = self._build_mock_group_info({})
        self.mixin._process_group(mock_group_info)
        mock_super.assert_called_once()
