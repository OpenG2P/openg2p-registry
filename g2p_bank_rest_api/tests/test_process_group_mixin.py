from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProcessGroupMixin(TransactionCase):
    def setUp(self):
        super().setUp()
        self.mixin = self.env["process_group.rest.mixin"]

        # Mocking group_info object
        self.mock_group_info = MagicMock()
        self.mock_group_info.model_dump.return_value = {"bank_ids": []}

    @patch("odoo.models.Model.sudo")
    def test_process_group_no_bank_ids(self, mock_sudo):
        # Test _process_group when no bank_ids are provided
        result = self.mixin._process_group(self.mock_group_info)
        self.assertNotIn("bank_ids", result)

    @patch("odoo.models.Model.sudo")
    def test_process_group_with_bank_ids(self, mock_sudo):
        # Test _process_group with valid bank_ids
        bank_name = "TEST_BANK_NAME"
        acc_number = "1112223334"

        # Mock bank_ids in group_info
        self.mock_group_info.model_dump.return_value = {
            "bank_ids": [MagicMock(bank_name=bank_name, acc_number=acc_number)]
        }
        self.mock_group_info.bank_ids = self.mock_group_info.model_dump()["bank_ids"]

        # Mock return for bank search
        mock_bank_model = mock_sudo.return_value.env["res.bank"]
        mock_bank_model.search.return_value = [MagicMock(id=1)]

        result = self.mixin._process_group(self.mock_group_info)

        self.assertIn("bank_ids", result)
        self.assertEqual(len(result["bank_ids"]), 1)
        self.assertEqual(result["bank_ids"][0][2]["acc_number"], acc_number)
        mock_sudo.assert_called()

    @patch("odoo.models.Model.sudo")
    def test_process_group_creates_new_bank(self, mock_sudo):
        # Test _process_group when a new bank needs to be created
        bank_name = "TEST_BANK_NAME"
        acc_number = "9876543210"

        self.mock_group_info.model_dump.return_value = {
            "bank_ids": [MagicMock(bank_name=bank_name, acc_number=acc_number)]
        }
        self.mock_group_info.bank_ids = self.mock_group_info.model_dump()["bank_ids"]

        # Mock bank creation and search
        mock_bank_model = mock_sudo.return_value.env["res.bank"]
        mock_search_result = []
        mock_bank_model.search.return_value = mock_search_result  # Empty search result
        mock_created_bank = MagicMock(id=2)
        mock_bank_model.create.return_value = mock_created_bank  # Simulate created bank

        result = self.mixin._process_group(self.mock_group_info)

        self.assertIn("bank_ids", result)
        self.assertEqual(len(result["bank_ids"]), 1)
        self.assertEqual(result["bank_ids"][0][2]["acc_number"], acc_number)
        mock_sudo.assert_called()
