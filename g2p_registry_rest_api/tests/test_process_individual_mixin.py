from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged

from ..exceptions.base_exception import G2PApiValidationError
from ..models.process_individual_mixin import ProcessIndividualMixin


@tagged("post_install", "-at_install")
class TestProcessIndividualMixin(TransactionCase):
    def setUp(self):
        super().setUp()
        self.mixin = self.env["process_individual.rest.mixin"]

        self.mock_individual = MagicMock()
        self.mock_individual.model_dump.return_value = {"ids": [], "phone_numbers": []}

    def test_process_individual_no_ids(self):
        # Test _process_individual when no ids are provided
        result = self.mixin._process_individual(self.mock_individual)
        self.assertNotIn("reg_ids", result)

    def test_process_individual_no_phone_numbers(self):
        # Test _process_individual when no phone numbers are provided
        result = self.mixin._process_individual(self.mock_individual)
        self.assertNotIn("phone_number_ids", result)

    @patch.object(ProcessIndividualMixin, "_process_ids", return_value=[1, 2, 3])
    def test_process_individual_with_ids(self, mock_process_ids):
        # Test _process_individual with ids
        self.mock_individual.ids_info = MagicMock()
        self.mock_individual.ids_info.return_value = {"id": 1}

        result = self.mixin._process_individual(self.mock_individual)
        self.assertIn("reg_ids", result)
        self.assertEqual(result["reg_ids"], [1, 2, 3])

    @patch.object(ProcessIndividualMixin, "_process_phones", return_value=(["1234567890"], "1234567890"))
    def test_process_individual_with_phones(self, mock_process_phones):
        # Test _process_individual with phone numbers
        self.mock_individual.ids_info = MagicMock()
        self.mock_individual.ids_info.return_value = {"phone": "1234567890"}

        result = self.mixin._process_individual(self.mock_individual)
        self.assertIn("phone", result)
        self.assertEqual(result["phone"], "1234567890")
        self.assertIn("phone_number_ids", result)
        self.assertEqual(result["phone_number_ids"], ["1234567890"])

    def test_process_individual_with_gender(self):
        # Test _process_individual with gender
        # Create a gender type in the db
        gender_type = self.env["gender.type"].create({"code": "male", "value": "Male"})

        self.mock_individual.gender = "male"

        result = self.mixin._process_individual(self.mock_individual)
        self.assertIn("gender", result)
        self.assertEqual(result["gender"], gender_type.value)

    def test_process_individual_without_gender(self):
        # Test _process_individual without gender
        self.mock_individual.gender = None

        result = self.mixin._process_individual(self.mock_individual)
        self.assertNotIn("gender", result)

    def test_process_ids_raises_error_for_nonexistent_id_type(self):
        # Test _process_ids raises error when the ID type does not exist
        self.mock_individual.ids = [MagicMock(id_type="Nonexistent ID Type")]
        with self.assertRaises(G2PApiValidationError):
            self.mixin._process_ids(self.mock_individual)

    def test_process_phones_with_primary_phone(self):
        # Test _process_phones with a primary phone number
        self.mock_individual.phone_numbers = [MagicMock(phone_no="1234567890")]
        phone_numbers, primary_phone = self.mixin._process_phones(self.mock_individual)
        self.assertEqual(primary_phone, "1234567890")
        self.assertEqual(len(phone_numbers), 1)
