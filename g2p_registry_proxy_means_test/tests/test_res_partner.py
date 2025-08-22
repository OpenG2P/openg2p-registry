from unittest.mock import patch

from odoo.tests import TransactionCase


class TestResPartner(TransactionCase):
    def setUp(self):
        super().setUp()
        self.group_kind = self.env["g2p.group.kind"].create({"name": "Test Kind"})

        self.pmt_params = self.env["g2p.proxy.means.test.params"].create(
            {"pmt_name": "Test PMT", "target": "individual", "kind": self.group_kind.id}
        )

        self.pmt_line = self.env["g2p.proxy.means.test.line"].create(
            {"pmt_id": self.pmt_params.id, "pmt_field": "income", "pmt_weightage": 0.5}
        )

        self.partner = self.env["res.partner"].create(
            {"name": "Test Partner", "kind": self.group_kind.id, "income": 1000, "is_group": False}
        )

    def test_compute_pmt_score(self):
        self.partner._compute_pmt_score()
        self.assertEqual(self.partner.pmt_score, 500)

    def test_compute_pmt_score_group(self):
        group_pmt = self.env["g2p.proxy.means.test.params"].create(
            {"pmt_name": "Group PMT", "target": "group", "kind": self.group_kind.id}
        )

        self.env["g2p.proxy.means.test.line"].create(
            {"pmt_id": group_pmt.id, "pmt_field": "income", "pmt_weightage": 0.75}
        )

        group_partner = self.env["res.partner"].create(
            {"name": "Test Group", "kind": self.group_kind.id, "income": 1000, "is_group": True}
        )

        group_partner._compute_pmt_score()
        self.assertEqual(group_partner.pmt_score, 750)

    def test_compute_pmt_score_no_params(self):
        self.env["g2p.proxy.means.test.params"].search([]).unlink()

        self.partner._compute_pmt_score()
        self.assertEqual(self.partner.pmt_score, 0)

    def test_compute_existing_pmt_scores(self):
        partner2 = self.env["res.partner"].create(
            {"name": "Test Partner 2", "kind": self.group_kind.id, "income": 2000}
        )

        self.env["res.partner"].compute_existing_pmt_scores()

        self.assertEqual(self.partner.pmt_score, 500)
        self.assertEqual(partner2.pmt_score, 1000)

    def test_write_triggers_pmt_computation(self):
        with patch.object(type(self.partner), "_compute_pmt_score") as mock_compute:
            self.partner.write({"income": 2000})
            mock_compute.assert_called()
