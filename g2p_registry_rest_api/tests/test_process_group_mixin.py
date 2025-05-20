from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged

from ..exceptions.base_exception import G2PApiValidationError
from ..models.process_individual_mixin import ProcessIndividualMixin


@tagged("post_install", "-at_install")
class TestProcessGroupMixin(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create an instance of the mixin class to test
        self.mixin = self.env["process_group.rest.mixin"]

        # Mock group info object
        self.mock_group = MagicMock()
        self.mock_group.model_dump.return_value = {"group_ids": []}

    def test_process_group_no_kind(self):
        # Test _process_group when no kind is provided
        self.mock_group.kind = None
        result = self.mixin._process_group(self.mock_group)
        self.assertNotIn("kind", result, "kind should not be in the result when absent.")

    def test_process_group_with_existing_kind(self):
        # Test _process_group when the kind already exists
        existing_kind = self.env["g2p.group.kind"].create({"name": "Test Kind"})

        self.mock_group.kind = "Test Kind"

        result = self.mixin._process_group(self.mock_group)

        self.assertEqual(result["kind"], existing_kind.id)

    def test_process_group_raises_error_for_nonexistent_kind(self):
        # Test _process_group raises error when the kind does not exist
        self.mock_group.kind = "Nonexistent Kind"
        with self.assertRaises(G2PApiValidationError):
            self.mixin._process_group(self.mock_group)

    @patch.object(ProcessIndividualMixin, "_process_ids", return_value=[1, 2, 3])
    def test_process_group_with_ids(self, mock_process_ids):
        # Test _process_group with ids
        self.env["g2p.group.kind"].create({"name": "Test Kind"})
        self.mock_group.kind = "Test Kind"

        self.mock_group.ids_info = MagicMock()
        self.mock_group.ids_info.return_value = {"id": 1}

        result = self.mixin._process_group(self.mock_group)
        self.assertIn("reg_ids", result)
        self.assertEqual(result["reg_ids"], [1, 2, 3])

    @patch.object(ProcessIndividualMixin, "_process_phones", return_value=(["1234567890"], "1234567890"))
    def test_process_group_with_phones(self, mock_process_phones):
        # Test _process_group with phone numbers
        self.env["g2p.group.kind"].create({"name": "Test Kind"})
        self.mock_group.kind = "Test Kind"

        self.mock_group.ids_info = MagicMock()
        self.mock_group.ids_info.return_value = {"phone": "1234567890"}

        result = self.mixin._process_group(self.mock_group)
        self.assertIn("phone", result)
        self.assertEqual(result["phone"], "1234567890")
        self.assertIn("phone_number_ids", result)
        self.assertEqual(result["phone_number_ids"], ["1234567890"])
