from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestG2PGender(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gender_type_model = cls.env["gender.type"]

    def test_01_empty_code_constraint(self):
        with self.assertRaises(ValidationError) as context:
            self.gender_type_model.create({"code": "", "value": "Some Value"})
        self.assertEqual(
            str(context.exception),
            "Gender type should not empty.",
            "Validation error message is not as expected.",
        )

    def test_02_unique_code_constraint(self):
        self.gender_type_model.create({"code": "male", "value": "Male"})

        with self.assertRaises(ValidationError):
            self.gender_type_model.create({"code": "male", "value": "Another Male"})

    def test_03_unique_code_constraint_different_records(self):
        self.gender_type_model.create({"code": "male", "value": "Male"})
        self.gender_type_model.create({"code": "female", "value": "Female"})
