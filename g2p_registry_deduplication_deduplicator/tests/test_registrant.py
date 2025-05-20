from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRegistrant(TransactionCase):
    def setUp(self):
        super().setUp()
        self.registrant = self.env["res.partner"].create({"name": "Test Registrant"})

    def test_view_deduplicator_duplicates(self):
        # Test the view_deduplicator_duplicates method.
        result = self.registrant.view_deduplicator_duplicates()
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertEqual(
            result["tag"],
            "g2p_registry_deduplication_deduplicator.view_duplicates_client_action",
        )
        self.assertEqual(result["target"], "new")
        self.assertEqual(result["name"], "Duplicates")
        self.assertEqual(result["params"]["record_id"], self.registrant.id)
        self.assertEqual(result["context"], {})
