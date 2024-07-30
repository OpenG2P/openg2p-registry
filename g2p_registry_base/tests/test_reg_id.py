from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestG2PRegistrantID(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_model = self.env["res.partner"]
        self.id_type_model = self.env["g2p.id.type"]
        self.reg_id_model = self.env["g2p.reg.id"]

    def test_01_display_name(self):
        partner = self.partner_model.create({"name": "Test Registrant", "is_registrant": True})
        id_type = self.id_type_model.create({"name": "Test ID Type", "id_validation": "[0-9]+"})

        reg_id = self.reg_id_model.create(
            {"partner_id": partner.id, "id_type": id_type.id, "value": "123456" ,"status":"valid", "description":"Due to API"}
        )

        # Call the _compute_display_name method
        reg_id._compute_display_name()

        # Check if the display name is as expected
        expected_display_name = "Test Registrant"
        self.assertEqual(
            reg_id.display_name,
            expected_display_name,
            "Display name is not as expected.",
        )

    def test_02_create_registrant_id(self):
        partner = self.partner_model.create({"name": "Test Registrant", "is_registrant": True})
        id_type = self.id_type_model.create({"name": "Test ID Type", "id_validation": "[0-9]+"})

        reg_id = self.reg_id_model.create(
            {"partner_id": partner.id, "id_type": id_type.id, "value": "123456", "status":"valid", "description":"Due to API"}
        )
        self.assertEqual(reg_id.value, "123456", "Registrant ID value is not as expected.")

    def test_03_invalid_id_value(self):
        partner = self.partner_model.create({"name": "Test Registrant", "is_registrant": True})
        id_type = self.id_type_model.create({"name": "Test ID Type", "id_validation": "[0-9]+"})

        with self.assertRaises(ValidationError) as context:
            self.reg_id_model.create({"partner_id": partner.id, "id_type": id_type.id, "value": "abc", "status":"valid", "description":"Due to API"})

        self.assertIn("The provided Test ID Type ID 'abc' is invalid.", str(context.exception))

    def test_04_name_search(self):
        partner = self.partner_model.create({"name": "Test Partner", "is_registrant": True})
        id_type = self.id_type_model.create({"name": "Test ID Type"})
        reg_id = self.reg_id_model.create(
            {"partner_id": partner.id, "id_type": id_type.id, "value": "Test Value","status":"valid", "description":"Due to API"}
        )
        search_result = self.reg_id_model._name_search("Test Partner")
        self.assertIn(reg_id.id, search_result, "Expected record not found in search result")


@tagged("post_install", "-at_install")
class TestG2PIDType(TransactionCase):
    def setUp(self):
        super().setUp()
        self.id_type_model = self.env["g2p.id.type"]

    def test_01_create_id_type(self):
        id_type = self.id_type_model.create({"name": "Test ID Type", "id_validation": "[0-9]+"})
        self.assertEqual(id_type.name, "Test ID Type", "ID Type name is not as expected.")

    def test_02_empty_id_type_name(self):
        with self.assertRaises(ValidationError) as context:
            self.id_type_model.create({"name": "", "id_validation": "[0-9]+"})

        self.assertIn("Id type should not empty", str(context.exception))

    def test_03_duplicate_id_type_name(self):
        self.id_type_model.create({"name": "Test ID Type", "id_validation": "[0-9]+"})

        with self.assertRaises(ValidationError) as context:
            self.id_type_model.create({"name": "Test ID Type", "id_validation": "[0-9]+"})

        self.assertIn("Id type already exists", str(context.exception))
