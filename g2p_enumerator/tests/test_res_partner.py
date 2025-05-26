import datetime

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestG2PRegistrant(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.enumerator = cls.env["g2p.enumerator"].create(
            {
                "enumerator_user_id": "TEST001",
                "data_collection_date": "2024-01-01",
            }
        )

    def test_create_partner_with_eid(self):
        # Test partner creation with eid
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "eid": "TEST123",
                "is_registrant": True,
            }
        )
        self.assertEqual(partner.eid, "TEST123")

    def test_create_partner_generate_eid(self):
        # Test eid generation for supplier partner creation
        partner = self.env["res.partner"].create(
            {
                "name": "Test Supplier",
                "supplier_rank": 1,
            }
        )
        self.assertNotEqual(partner.eid, "New")
        self.assertNotEqual(partner.eid, False)

    def test_create_partner_no_eid_generation(self):
        # Test eid for non supplier partner creation
        partner = self.env["res.partner"].create(
            {
                "name": "Test Customer",
                "supplier_rank": 0,
            }
        )
        self.assertEqual(partner.eid, "New")

    def test_enumerator_fields(self):
        # Test enumerator field on partner creation
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "enumerator_id": self.enumerator.id,
            }
        )

        self.assertEqual(partner.enumerator_user_id, "TEST001")
        self.assertEqual(partner.data_collection_date, datetime.date(2024, 1, 1))

    def test_compute_creator_eid_no_creator(self):
        # Test creator_eid computation
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        partner.create_uid = False
        partner._compute_creator_eid()

        self.assertFalse(partner.creator_eid)

    def test_generate_eid(self):
        # Test generate eid method
        partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        generated_eid = partner.generate_eid()

        self.assertTrue(generated_eid)
        self.assertNotEqual(generated_eid, "New")
