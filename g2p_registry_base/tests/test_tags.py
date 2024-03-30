from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestG2PRegistrantTags(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestG2PRegistrantTags, cls).setUpClass()
        cls.tag_model = cls.env["g2p.registrant.tags"]

    def test_create_registrant_tag(self):
        tag_name = "Test Tag"
        tag = self.tag_model.create({"name": tag_name})

        self.assertEqual(tag.name, tag_name)
        self.assertTrue(tag.active)

    def test_create_duplicate_registrant_tag(self):
        tag_name = "Test Tag"
        self.tag_model.create({"name": tag_name})

        with self.assertRaises(ValidationError):
            self.tag_model.create({"name": tag_name})

    def test_create_tag_with_empty_name(self):
        with self.assertRaises(ValidationError):
            self.tag_model.create({"name": ""})

    def test_check_name_constraint_case_insensitive(self):
        tag_name = "Test Tag"
        self.tag_model.create({"name": tag_name.lower()})

        with self.assertRaises(ValidationError):
            self.tag_model.create({"name": tag_name.upper()})
