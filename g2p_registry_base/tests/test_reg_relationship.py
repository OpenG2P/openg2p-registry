from odoo import _
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestG2PRegistrantRelationship(TransactionCase):
    def setUp(self):
        super().setUp()
        self.reg_rel_model = self.env["g2p.reg.rel"]
        self.rel_model = self.env["g2p.relationship"]
        self.partner_model = self.env["res.partner"]
        self.group_partner = self.partner_model.create(
            {"is_group": True, "is_registrant": True, "name": "Test Group"}
        )
        self.individual_partner = self.partner_model.create(
            {"is_group": False, "is_registrant": True, "name": "Test Individual"}
        )

    def test_constraints(self):
        rel_type = self.rel_model.create(
            {
                "name": "Test Relationship",
                "name_inverse": "Inverse Test Relationship",
                "source_type": "g",
                "destination_type": "i",
            }
        )
        rel = self.reg_rel_model.create(
            {
                "source": self.group_partner.id,
                "destination": self.individual_partner.id,
                "relation": rel_type.id,
            }
        )

        with self.assertRaisesRegex(Exception, "Registrant 1 and Registrant 2 cannot be the same."):
            rel_type.destination_type = "g"
            rel.write({"source": self.group_partner.id, "destination": self.group_partner.id})

        with self.assertRaisesRegex(Exception, "The starting date cannot be after the ending date."):
            rel.write({"start_date": "2023-01-01", "end_date": "2022-01-01"})

        with self.assertRaisesRegex(Exception, "There is already a similar relation with overlapping dates"):
            rel_type.destination_type = "i"
            rel.destination = self.individual_partner.id
            rel2 = self.reg_rel_model.create(
                {
                    "source": self.group_partner.id,
                    "destination": self.individual_partner.id,
                    "relation": rel_type.id,
                }
            )
            rel2.write({"start_date": "2022-01-01", "end_date": "2023-01-01"})

        with self.assertRaisesRegex(Exception, "This registrant is not applicable for this relation type."):
            rel.write(
                {
                    "relation": self.rel_model.create(
                        {
                            "name": "Invalid Relationship",
                            "name_inverse": "Inverse Invalid Relationship",
                            "source_type": "i",
                            "destination_type": "g",
                        }
                    ).id
                }
            )

    def test_compute_display_name(self):
        rel_type = self.rel_model.create(
            {
                "name": "Test Relationship",
                "name_inverse": "Inverse Test Relationship",
                "source_type": "g",
                "destination_type": "i",
            }
        )
        rel = self.reg_rel_model.create(
            {
                "source": self.group_partner.id,
                "destination": self.individual_partner.id,
                "relation": rel_type.id,
            }
        )

        rel._compute_display_name()
        self.assertEqual(rel.display_name, "Test Group / Test Individual")

    # def test_name_search(self):
    #     rel_type = self.rel_model.create(
    #         {
    #             "name": "Test Relationship",
    #             "name_inverse": "Inverse Test Relationship",
    #             "source_type": "g",
    #             "destination_type": "i",
    #         }
    #     )
    #     rel = self.reg_rel_model.create(
    #         {
    #             "source": self.group_partner.id,
    #             "destination": self.individual_partner.id,
    #             "relation": rel_type.id,
    #         }
    #     )

    #     result = rel._name_search("Test", operator="ilike")
    #     self.assertIn(rel.id, [r.id for r in result])

    def test_disable_relationship(self):
        rel_type = self.rel_model.create(
            {
                "name": "Test Relationship",
                "name_inverse": "Inverse Test Relationship",
                "source_type": "g",
                "destination_type": "i",
            }
        )
        rel = self.reg_rel_model.create(
            {
                "source": self.group_partner.id,
                "destination": self.individual_partner.id,
                "relation": rel_type.id,
            }
        )

        rel.disable_relationship()
        self.assertIsNotNone(rel.disabled)
        self.assertIsNotNone(rel.disabled_by)

    def test_enable_relationship(self):
        rel_type = self.rel_model.create(
            {
                "name": "Test Relationship",
                "name_inverse": "Inverse Test Relationship",
                "source_type": "g",
                "destination_type": "i",
            }
        )
        rel = self.reg_rel_model.create(
            {
                "source": self.group_partner.id,
                "destination": self.individual_partner.id,
                "relation": rel_type.id,
                "disabled": "2023-01-01",
                "disabled_by": self.env.user.id,
            }
        )

        rel.enable_relationship()
        self.assertTrue(not rel.disabled)
        self.assertTrue(not rel.disabled_by)

    def test_open_relationship_forms(self):
        rel_type = self.rel_model.create(
            {
                "name": "Test Relationship",
                "name_inverse": "Inverse Test Relationship",
                "source_type": "g",
                "destination_type": "i",
            }
        )
        rel = self.reg_rel_model.create(
            {
                "source": self.group_partner.id,
                "destination": self.individual_partner.id,
                "relation": rel_type.id,
            }
        )

        form1 = rel.open_relationship1_form()
        self.assertEqual(form1["res_model"], "res.partner")
        self.assertEqual(form1["res_id"], self.group_partner.id)
        self.assertEqual(form1["view_id"], self.env.ref("g2p_registry_group.view_groups_form").id)

        form2 = rel.open_relationship2_form()
        self.assertEqual(form2["res_model"], "res.partner")
        self.assertEqual(form2["res_id"], self.individual_partner.id)
        self.assertEqual(
            form2["view_id"],
            self.env.ref("g2p_registry_individual.view_individuals_form").id,
        )


class TestG2PRelationship(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rel_model = cls.env["g2p.relationship"]

    def test_get_partner_types(self):
        partner_types = self.rel_model.get_partner_types()
        self.assertEqual(partner_types, [("g", _("Group")), ("i", _("Individual"))])

    def test_check_name_constraint(self):
        with self.assertRaisesRegex(Exception, "Name should not be empty."):
            self.rel_model.create(
                {
                    "name": "",
                    "name_inverse": "Inverse Name",
                    "source_type": "g",
                    "destination_type": "i",
                }
            )

    def test_create_relationship(self):
        rel = self.rel_model.create(
            {
                "name": "Test Relationship",
                "name_inverse": "Inverse Test Relationship",
                "source_type": "g",
                "destination_type": "i",
            }
        )
        self.assertTrue(rel.id)
