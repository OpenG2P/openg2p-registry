from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProcessSocialIndividualMixin(TransactionCase):
    def setUp(self):
        super().setUp()
        self.mixin = self.env["process_individual.rest.mixin"]

    def _build_mock_individual(self, fields):
        mock_ind = MagicMock()
        mock_ind.model_dump.return_value = fields
        return mock_ind

    @patch(
        "odoo.addons.g2p_registry_rest_api.models.process_individual_mixin.ProcessIndividualMixin._process_individual",
        return_value={"name": "Test Person"},
    )
    def test_process_individual_with_all_fields(self, mock_super):
        input_fields = {
            "education_level": "Graduate",
            "employment_status": "Employed",
            "marital_status": "Single",
            "occupation": "Teacher",
            "income": 45000,
        }

        mock_individual = self._build_mock_individual(input_fields)
        result = self.mixin._process_individual(mock_individual)

        # Ensure all expected fields are added
        for key in input_fields:
            self.assertIn(key, result)
            self.assertEqual(result[key], input_fields[key])

    @patch(
        "odoo.addons.g2p_registry_rest_api.models.process_individual_mixin.ProcessIndividualMixin._process_individual",
        return_value={"name": "Test Person"},
    )
    def test_process_individual_with_partial_fields(self, mock_super):
        input_fields = {
            "education_level": "Primary",
            "income": 12000,
        }

        mock_individual = self._build_mock_individual(input_fields)
        result = self.mixin._process_individual(mock_individual)

        self.assertEqual(result["education_level"], "Primary")
        self.assertEqual(result["income"], 12000)
        self.assertNotIn("occupation", result)
        self.assertNotIn("employment_status", result)

    @patch(
        "odoo.addons.g2p_registry_rest_api.models.process_individual_mixin.ProcessIndividualMixin._process_individual",
        return_value={"name": "Test Person"},
    )
    def test_process_individual_with_no_optional_fields(self, mock_super):
        mock_individual = self._build_mock_individual({})
        result = self.mixin._process_individual(mock_individual)

        self.assertEqual(result, {"name": "Test Person"})

    @patch(
        "odoo.addons.g2p_registry_rest_api.models.process_individual_mixin.ProcessIndividualMixin._process_individual",
        return_value={"name": "Test Person"},
    )
    def test_super_method_called_once(self, mock_super):
        mock_individual = self._build_mock_individual({})
        self.mixin._process_individual(mock_individual)
        mock_super.assert_called_once()
