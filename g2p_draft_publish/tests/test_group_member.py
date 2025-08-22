from odoo.tests import TransactionCase


class TestDraftGroupAddMembersWizard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Draft = self.env["draft.record"]
        self.Wizard = self.env["draft.group.add.members.wizard"]

        self.individual_1 = self.Draft.create(
            {"given_name": "Alice", "family_name": "Wonder", "is_group": False}
        )
        self.individual_2 = self.Draft.create(
            {"given_name": "Bob", "family_name": "Builder", "is_group": False}
        )

        self.group = self.Draft.create(
            {
                "name": "Sample Group",
                "is_group": True,
                "group_member_ids_json": [self.individual_1.id, self.individual_2.id],
            }
        )

    def test_wizard_default_get(self):
        """Ensure wizard loads existing group and member lines."""
        wizard = self.Wizard.with_context(default_group_id=self.group.id).create({})
        self.assertEqual(wizard.group_id.id, self.group.id)
        self.assertEqual(len(wizard.line_ids), 2)

        member_ids = {line.member_id.id for line in wizard.line_ids}
        self.assertSetEqual(member_ids, {self.individual_1.id, self.individual_2.id})

    def test_wizard_action_save_members(self):
        """Ensure action_save_members stores updated member list to group."""
        wizard = self.Wizard.with_context(default_group_id=self.group.id).create(
            {"line_ids": [(0, 0, {"member_id": self.individual_1.id})]}
        )

        wizard.action_save_members()
        self.assertEqual(self.group.group_member_ids_json, [self.individual_1.id])
