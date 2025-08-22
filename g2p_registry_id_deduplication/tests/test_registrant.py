from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestResPartnerIDDeduplication(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_model = self.env["res.partner"]
        self.id_type_model = self.env["g2p.id.type"]
        self.reg_id_model = self.env["g2p.reg.id"]
        self.group_membership_model = self.env["g2p.group.membership"]
        self.dedup_grp_kind_config_model = self.env["g2p.group.kind.deduplication.config"]
        self.group_kind_model = self.env["g2p.group.kind"]
        self.config_parameter_model = self.env["ir.config_parameter"].sudo()
        self.individual_1 = self.partner_model.create(
            {"name": "Individual 1", "is_registrant": True, "is_group": False}
        )
        self.individual_2 = self.partner_model.create(
            {"name": "Individual 2", "is_registrant": True, "is_group": False}
        )
        self.group_kind = self.group_kind_model.create({"name": "Test Kind"})
        self.group_1 = self.partner_model.create(
            {
                "name": "Group 1",
                "is_registrant": True,
                "is_group": True,
                "kind": self.group_kind.id,
                "group_membership_ids": [(0, 0, {"individual": self.individual_1.id})],
            }
        )
        self.group_2 = self.partner_model.create(
            {
                "name": "Group 2",
                "is_registrant": True,
                "is_group": True,
                "kind": self.group_kind.id,
                "group_membership_ids": [(0, 0, {"individual": self.individual_1.id})],
            }
        )

        self.id_type_1 = self.id_type_model.create({"name": "Household ID"})
        self.id_type_2 = self.id_type_model.create({"name": "National ID"})

        self.reg_id_1 = self.reg_id_model.create(
            {
                "partner_id": self.individual_1.id,
                "id_type": self.id_type_2.id,
                "value": 12345,
                "status": "invalid",
                "description": "Failed",
            }
        )
        self.reg_id_2 = self.reg_id_model.create(
            {
                "partner_id": self.individual_2.id,
                "id_type": self.id_type_2.id,
                "value": 12345,
                "status": "invalid",
                "description": "Failed",
            }
        )
        self.reg_id_3 = self.reg_id_model.create(
            {
                "partner_id": self.group_1.id,
                "id_type": self.id_type_1.id,
                "value": 123,
                "status": "invalid",
                "description": "Failed",
            }
        )
        self.reg_id_4 = self.reg_id_model.create(
            {
                "partner_id": self.group_2.id,
                "id_type": self.id_type_1.id,
                "value": 123,
                "status": "invalid",
                "description": "Failed",
            }
        )

        self.grp_dedup_config = self.dedup_grp_kind_config_model.create(
            {
                "kind_id": self.group_kind.id,
                "id_type_ids": [self.id_type_1.id],
            }
        )

        self.config_parameter_model.set_param(
            "g2p_registry_id_deduplication.ind_deduplication_id_types_ids", f"[{self.id_type_2.id}]"
        )
        self.config_parameter_model.set_param(
            "g2p_registry_id_deduplication.grp_deduplication_id_types_ids", f"[{self.grp_dedup_config.id}]"
        )

    def test_deduplicate_registrants_individuals(self):
        self.partner_model.with_context(default_is_group=False).deduplicate_registrants()
        self.assertTrue(self.individual_1.is_duplicated)
        self.assertTrue(self.individual_2.is_duplicated)
        self.assertFalse(self.group_1.is_duplicated)
        self.assertFalse(self.group_2.is_duplicated)

    def test_deduplicate_registrants_groups(self):
        self.partner_model.with_context(default_is_group=True).deduplicate_registrants()
        self.assertFalse(self.individual_1.is_duplicated)
        self.assertFalse(self.individual_2.is_duplicated)
        self.assertTrue(self.group_1.is_duplicated)
        self.assertTrue(self.group_2.is_duplicated)

    def test_deduplicate_registrants_missing_configuration(self):
        self.config_parameter_model.set_param(
            "g2p_registry_id_deduplication.ind_deduplication_id_types_ids", "[]"
        )
        with self.assertRaises(UserError, msg="Deduplication is not configured"):
            self.partner_model.with_context(default_is_group=False).deduplicate_registrants()

    def test_reset_duplicate_flag(self):
        self.partner_model.with_context(default_is_group=False).reset_duplicate_flag(False)
        self.assertFalse(self.individual_1.is_duplicated)
        self.assertFalse(self.individual_2.is_duplicated)
        self.assertFalse(self.group_1.is_duplicated)
        self.assertFalse(self.group_2.is_duplicated)

    def test_get_id_types_with_kind_individual(self):
        id_types = self.partner_model.get_id_types_with_kind("ind_deduplication_id_types_ids", is_group=False)
        self.assertIn(False, id_types)
        self.assertEqual(id_types[False], f"('{self.id_type_2.name}')")

    def test_get_id_types_with_kind_group(self):
        id_types = self.partner_model.get_id_types_with_kind("grp_deduplication_id_types_ids", is_group=True)
        self.assertIn(self.group_kind.name, id_types)
        self.assertEqual(id_types[self.group_kind.name], f"('{self.id_type_1.name}')")
