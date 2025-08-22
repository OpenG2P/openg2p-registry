from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestSRProxyMeanTestParams(TransactionCase):
    def setUp(self):
        super().setUp()
        self.group_kind = self.env["g2p.group.kind"].create({"name": "Test Kind"})

        self.pmt_params = self.env["g2p.proxy.means.test.params"].create(
            {"pmt_name": "Test PMT", "target": "individual", "kind": self.group_kind.id}
        )

    def test_create_duplicate_pmt(self):
        with self.assertRaises(ValidationError):
            self.env["g2p.proxy.means.test.params"].create(
                {"pmt_name": "Duplicate PMT", "target": "individual", "kind": self.group_kind.id}
            )

    def test_write_duplicate_pmt(self):
        other_pmt = self.env["g2p.proxy.means.test.params"].create(
            {"pmt_name": "Other PMT", "target": "group", "kind": self.group_kind.id}
        )

        with self.assertRaises(ValidationError):
            other_pmt.write({"target": "individual"})

    def test_onchange_target(self):
        self.pmt_params.target = "group"
        self.pmt_params._onchange_target()
        self.assertFalse(self.pmt_params.target_name)

        self.pmt_params.target = "individual"
        self.pmt_params._onchange_target()
        self.assertTrue(self.pmt_params.target_name)

    def test_unlink(self):
        partner = self.env["res.partner"].create({"name": "Test Partner", "kind": self.group_kind.id})

        self.env["g2p.proxy.means.test.line"].create(
            {"pmt_id": self.pmt_params.id, "pmt_field": "income", "pmt_weightage": 1.0}
        )

        self.pmt_params.unlink()

        self.assertEqual(partner.pmt_score, 0)

    def test_compute_related_partners_pmt_score(self):
        partner = self.env["res.partner"].create(
            {"name": "Test Partner", "kind": self.group_kind.id, "income": 1000}
        )

        self.env["g2p.proxy.means.test.line"].create(
            {"pmt_id": self.pmt_params.id, "pmt_field": "income", "pmt_weightage": 0.5}
        )

        self.pmt_params.compute_related_partners_pmt_score()
        self.assertEqual(partner.pmt_score, 500)

    def test_invalid_computation_conditions(self):
        invalid_pmt = self.env["g2p.proxy.means.test.params"].create({"pmt_name": False, "target": False})

        invalid_pmt.compute_related_partners_pmt_score()
