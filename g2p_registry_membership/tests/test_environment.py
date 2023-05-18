from odoo.tests import TransactionCase


class TestEnvironment(TransactionCase):
    def setUp(self):
        super().setUp()
        self._partners = self.env["res.partner"].create(
            [
                {
                    "name": "Partner 1",
                    "is_registrant": True,
                },
                {
                    "name": "Partner 2",
                    "is_registrant": True,
                },
                {
                    "name": "Partner 3",
                    "is_registrant": True,
                },
                {
                    "name": "Partner 4",
                    "is_registrant": True,
                },
                {
                    "name": "Partner 5",
                    "is_registrant": True,
                },
                {
                    "name": "Partner 6",
                    "is_registrant": True,
                },
                {
                    "name": "Partner 7",
                    "is_registrant": True,
                },
                {
                    "name": "Partner 8",
                    "is_registrant": True,
                },
                {
                    "name": "Partner 9",
                    "is_registrant": True,
                },
                {
                    "name": "Partner 10",
                    "is_registrant": True,
                },
                {
                    "name": "Partner 11",
                    "is_registrant": True,
                },
            ]
        )
        self.field_canary = self._partners._fields["force_recompute_canary"]

    def test_01_records_to_compute(self):
        self.env.add_to_compute(self.field_canary, self._partners[:5])
        fields_to_compute = self.env.fields_to_compute()
        self.assertNotIn(
            self.field_canary,
            fields_to_compute,
            "Canary Force Recompute should not be in fields to compute since "
            "the len of recompute records is 5!",
        )
        self.env.add_to_compute(self.field_canary, self._partners)
        fields_to_compute = self.env.fields_to_compute()
        self.assertIn(
            self.field_canary,
            fields_to_compute,
            "Canary Force Recompute should be in fields to compute "
            "since the len of recompute records is 11!",
        )

    def test_02_records_to_compute(self):
        field_z_ind_grp_num_individuals = self._partners._fields[
            "z_ind_grp_num_individuals"
        ]
        self.env.add_to_compute(self.field_canary, self._partners)
        self.env.add_to_compute(field_z_ind_grp_num_individuals, self._partners[5:])
        records_to_compute = self.env.records_to_compute(
            field_z_ind_grp_num_individuals
        )
        self.assertEqual(
            len(records_to_compute),
            len(self._partners),
            "Other fields recompute record should include all the Canary Force Recompute field "
            "since the len of compute record is 5!",
        )
        new_partner = self.env["res.partner"].create(
            {
                "name": "Partner 12",
                "is_registrant": True,
            }
        )
        new_partner |= self._partners[1:9]
        self.env.add_to_compute(self.field_canary, self._partners)
        self.env.add_to_compute(field_z_ind_grp_num_individuals, new_partner)
        records_to_compute = self.env.records_to_compute(
            field_z_ind_grp_num_individuals
        )
        self.assertTrue(
            bool(records_to_compute - self._partners),
            "Other fields recompute record should not include all the Canary Force Recompute field "
            "since the len of compute record is 11!",
        )
        self.assertTrue(
            bool(self._partners - records_to_compute),
            "Other fields recompute record should not include all the Canary Force Recompute field "
            "since the len of compute record is 11!",
        )
