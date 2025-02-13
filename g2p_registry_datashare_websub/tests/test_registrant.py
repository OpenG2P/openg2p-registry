from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRegistrant(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Model = self.env["res.partner"]

    def test_create_registrant(self):
        # Test creating a simple registrant
        vals = {
            "name": "Test Registrant",
            "is_registrant": True,
            "is_group": False,
        }
        rec = self.Model.create(vals)
        self.assertTrue(rec)

    def test_create_group_registrant(self):
        # Test creating a group registrant
        vals = {
            "name": "Test Group Registrant",
            "is_registrant": True,
            "is_group": True,
        }
        rec = self.Model.create(vals)
        self.assertTrue(rec)

    def test_write_registrant(self):
        # Test updating an existing registrant
        vals = {
            "name": "Test Registrant",
            "is_registrant": True,
            "is_group": False,
        }
        rec = self.Model.create(vals)
        self.assertTrue(rec)
        rec.write({"name": "Updated Registrant"})
        self.assertEqual(rec.name, "Updated Registrant")

    def test_write_group_registrant(self):
        # Test updating an existing group registrant
        vals = {
            "name": "Test Group Registrant",
            "is_registrant": True,
            "is_group": True,
        }
        rec = self.Model.create(vals)
        self.assertTrue(rec)
        rec.write({"name": "Updated Group Registrant"})
        self.assertEqual(rec.name, "Updated Group Registrant")

    def test_unlink_registrant(self):
        # Test deleting an existing registrant
        vals = {
            "name": "Test Registrant",
            "is_registrant": True,
            "is_group": False,
        }
        rec = self.Model.create(vals)
        rec_id = rec.id
        rec.unlink()
        self.assertFalse(self.Model.browse(rec_id).exists())

    def test_unlink_group_registrant(self):
        # Test deleting an existing group registrant
        vals = {
            "name": "Test Group Registrant",
            "is_registrant": True,
            "is_group": True,
        }
        rec = self.Model.create(vals)
        rec_id = rec.id
        rec.unlink()
        self.assertFalse(self.Model.browse(rec_id).exists())
