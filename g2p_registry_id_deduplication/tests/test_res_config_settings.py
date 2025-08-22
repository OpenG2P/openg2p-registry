from odoo.tests.common import TransactionCase
from odoo.tools.safe_eval import safe_eval


class TestRegistryConfig(TransactionCase):
    def setUp(self):
        super().setUp()
        self.registry_config_model = self.env["res.config.settings"]
        self.id_type_model = self.env["g2p.id.type"]
        self.grp_dedup_config_model = self.env["g2p.group.kind.deduplication.config"]
        self.id_type_1 = self.id_type_model.create({"name": "National ID"})
        self.id_type_2 = self.id_type_model.create({"name": "Household ID"})
        self.grp_dedup_config = self.grp_dedup_config_model.create(
            {
                "kind_id": self.env["g2p.group.kind"].create({"name": "Test Group Kind"}).id,
                "id_type_ids": [(6, 0, [self.id_type_1.id, self.id_type_2.id])],
            }
        )

    def test_set_and_get_values(self):
        config_settings = self.registry_config_model.create({})
        config_settings.grp_deduplication_id_types_ids = [(4, self.grp_dedup_config.id)]
        config_settings.ind_deduplication_id_types_ids = [(4, self.id_type_1.id), (4, self.id_type_2.id)]
        config_settings.set_values()
        config_settings.get_values()
        self.assertIn(self.grp_dedup_config.id, config_settings.grp_deduplication_id_types_ids.mapped("id"))
        self.assertIn(self.id_type_1.id, config_settings.ind_deduplication_id_types_ids.mapped("id"))
        self.assertIn(self.id_type_2.id, config_settings.ind_deduplication_id_types_ids.mapped("id"))

    def test_delete_id_type_updates_config(self):
        config_settings = self.registry_config_model.create({})
        config_settings.ind_deduplication_id_types_ids = [(4, self.id_type_1.id), (4, self.id_type_2.id)]
        config_settings.set_values()
        self.id_type_1.unlink()
        ir_config = self.env["ir.config_parameter"].sudo()
        updated_id_types_param = ir_config.get_param(
            "g2p_registry_id_deduplication.ind_deduplication_id_types_ids"
        )
        updated_id_types_ids = safe_eval(updated_id_types_param)
        self.assertNotIn(self.id_type_1.id, updated_id_types_ids)
        self.assertIn(self.id_type_2.id, updated_id_types_ids)

    def test_set_values_empty_ids(self):
        config_settings = self.registry_config_model.create({})
        config_settings.set_values()
        ir_config = self.env["ir.config_parameter"].sudo()
        ir_config.set_param("g2p_registry_id_deduplication.grp_deduplication_id_types_ids", "[]")
        ir_config.set_param("g2p_registry_id_deduplication.ind_deduplication_id_types_ids", "[]")
        grp_id_types_param = ir_config.get_param(
            "g2p_registry_id_deduplication.grp_deduplication_id_types_ids"
        )
        ind_id_types_param = ir_config.get_param(
            "g2p_registry_id_deduplication.ind_deduplication_id_types_ids"
        )
        self.assertEqual(grp_id_types_param, "[]")
        self.assertEqual(ind_id_types_param, "[]")

    def test_unlink_id_type_with_no_references(self):
        new_id_type = self.id_type_model.create({"name": "New ID Type"})
        self.assertTrue(new_id_type.exists(), "New ID Type should exist before unlinking.")
        new_id_type.unlink()
        self.assertFalse(
            self.id_type_model.browse(new_id_type.id).exists(),
            "New ID Type should not exist after unlinking.",
        )

    def test_unlink_id_type_with_references(self):
        config_settings = self.registry_config_model.create({})
        config_settings.ind_deduplication_id_types_ids = [(4, self.id_type_1.id)]
        config_settings.set_values()
        self.id_type_1.unlink()
