from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase


class TestSRProxyMeanTestLine(TransactionCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.group_kind = self.env["g2p.group.kind"].create({"name": "Test Kind"})

    def setUp(self):
        super().setUp()

        self.pmt_params = self.env["g2p.proxy.means.test.params"].create(
            {"pmt_name": "Test PMT", "target": "individual", "kind": self.group_kind.id, "target_name": True}
        )

        self.pmt_line = self.env["g2p.proxy.means.test.line"].create(
            {"pmt_id": self.pmt_params.id, "pmt_field": "income", "pmt_weightage": 1.0}
        )

    def tearDown(self):
        self.pmt_line.unlink()
        self.pmt_params.unlink()
        super().tearDown()

    def test_check_unique_field_weightage(self):
        with self.assertRaises(ValidationError):
            self.env["g2p.proxy.means.test.line"].create(
                {"pmt_id": self.pmt_params.id, "pmt_field": "income", "pmt_weightage": 2.0}
            )

    def test_get_fields_label(self):
        fields = self.pmt_line.get_fields_label()

        self.assertTrue(isinstance(fields, list))
        self.assertTrue(len(fields) > 0, "Should return at least one field")

        excluded_fields = {"pmt_score", "message_needaction_counter"}
        field_names = [f[0] for f in fields]
        for excluded in excluded_fields:
            self.assertNotIn(excluded, field_names)

        self.assertIn("income", field_names)

    def test_field_type_filtering(self):
        fields = self.pmt_line.get_fields_label()

        ir_fields = self.env["ir.model.fields"].search(
            [("model", "=", "res.partner"), ("name", "in", [f[0] for f in fields])]
        )

        for field in ir_fields:
            self.assertIn(field.ttype, ["integer", "float"])

        field_names = [f.name for f in ir_fields]
        self.assertIn("income", field_names)
