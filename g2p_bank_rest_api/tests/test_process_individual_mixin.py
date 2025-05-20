from unittest.mock import MagicMock

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProcessIndividualMixin(TransactionCase):
    def setUp(self):
        super().setUp()
        self.mixin = self.env["process_individual.rest.mixin"]

        # Mocking the registrant info object
        self.mock_individual = MagicMock()
        self.mock_individual.model_dump.return_value = {"bank_ids": []}

    def test_process_individual_no_bank_ids(self):
        # Test _process_individual when no bank_ids are provided
        result = self.mixin._process_individual(self.mock_individual)
        self.assertNotIn("bank_ids", result)

    def test_process_bank_ids_with_existing_bank(self):
        # Test _process_bank_ids when the bank already exists

        # Set up existing bank
        existing_bank = self.env["res.bank"].create({"name": "Test Bank"})

        # Mocking bank_ids
        self.mock_individual.bank_ids = [MagicMock(bank_name="Test Bank", acc_number="1234567890")]

        bank_ids_result = self.mixin._process_bank_ids(self.mock_individual)

        self.assertEqual(len(bank_ids_result), 1)
        self.assertEqual(bank_ids_result[0][2]["bank_id"], existing_bank.id)
        self.assertEqual(bank_ids_result[0][2]["acc_number"], "1234567890")

    def test_process_bank_ids_creates_new_bank(self):
        # Test _process_bank_ids when the bank does not exist
        bank_name = "New Test Bank"
        acc_number = "0987654321"

        # Ensure no bank exists initially
        bank_count_before = self.env["res.bank"].search_count([("name", "=", bank_name)])
        self.assertEqual(bank_count_before, 0)

        # Mocking bank_ids
        self.mock_individual.bank_ids = [MagicMock(bank_name=bank_name, acc_number=acc_number)]

        bank_ids_result = self.mixin._process_bank_ids(self.mock_individual)

        new_bank = self.env["res.bank"].search([("name", "=", bank_name)])
        self.assertEqual(len(new_bank), 1)
        self.assertEqual(bank_ids_result[0][2]["bank_id"], new_bank.id)
        self.assertEqual(bank_ids_result[0][2]["acc_number"], acc_number)

    def test_process_individual_with_bank_ids(self):
        # Test _process_individual with valid bank_ids
        bank_name = "Final Test Bank"
        acc_number = "5555555555"

        # Mocking bank_ids
        self.mock_individual.model_dump.return_value = {
            "bank_ids": [MagicMock(bank_name=bank_name, acc_number=acc_number)]
        }
        self.mock_individual.bank_ids = self.mock_individual.model_dump()["bank_ids"]

        result = self.mixin._process_individual(self.mock_individual)

        self.assertIn("bank_ids", result)
        self.assertEqual(len(result["bank_ids"]), 1)
        self.assertEqual(result["bank_ids"][0][2]["acc_number"], acc_number)

        # Verify the bank was created
        new_bank = self.env["res.bank"].search([("name", "=", bank_name)])
        self.assertEqual(len(new_bank), 1, "A bank should be created during processing.")
