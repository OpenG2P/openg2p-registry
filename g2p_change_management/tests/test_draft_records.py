import json
from datetime import date, datetime
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase


class TestWebSave(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Partner = self.env["res.partner"]

    def test_web_save_create(self):
        """Test the web_save method on a new res.partner record."""
        result = self.Partner.browse().web_save({"name": "Ged"}, {})
        partner_id = result[0]["id"]
        partner = self.env["res.partner"].browse(partner_id)
        self.assertTrue(partner.exists())
        self.assertEqual(partner.name, "Ged")
        self.assertEqual(len(result), 1)
        self.assertEqual(result, [{"id": partner.id}])

        result = self.Partner.browse().web_save({"name": "Ged"}, {"display_name": {}})
        new_partner_id = result[0]["id"]
        new_partner = self.env["res.partner"].browse(new_partner_id)
        self.assertEqual(result, [{"id": new_partner.id, "display_name": "Ged"}])

    def test_web_save_write(self):
        """Test the web_save method on an existing res.partner record."""
        partner = self.Partner.create({"name": "Old Name"})

        result = partner.web_save({"name": "New Name"}, {})
        self.assertEqual(result, [{"id": partner.id}])
        self.assertEqual(partner.name, "New Name")

        result = partner.web_save({"name": "Updated Name"}, {"display_name": {}})
        self.assertEqual(result, [{"id": partner.id, "display_name": "Updated Name"}])

    def test_web_save_with_next_id(self):
        """Test that web_save uses next_id to return the correct record."""
        partner = self.Partner.create({"name": "Before"})
        next_partner = self.Partner.create({"name": "After"})

        result = partner.web_save({"name": "Updated"}, {"display_name": {}}, next_id=next_partner.id)

        self.assertEqual(result[0]["id"], next_partner.id)
        self.assertEqual(result[0]["display_name"], "After")


class TestDraftRecord(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Draft = self.env["g2p.draft.record"]

    def test_create_individual_record(self):
        record = self.Draft.create(
            {
                "given_name": "John",
                "family_name": "Doe",
                "addl_name": "Middle",
                "gender": "male",
                "phone": "1234567890",
                "is_group": False,
            }
        )

        self.assertEqual(record.name, "JOHN DOE MIDDLE")
        data = json.loads(record.partner_data)
        self.assertEqual(data["given_name"], "John")
        self.assertEqual(data["phone_number_ids"][0][2]["phone_no"], "1234567890")

    def test_create_group_record(self):
        record = self.Draft.create({"name": "Test Group", "is_group": True})
        data = json.loads(record.partner_data)
        self.assertEqual(data["name"], "Test Group")
        self.assertTrue(data["is_group"])

    def test_action_change_state(self):
        record = self.Draft.create({"name": "Change State"})
        with patch("odoo.addons.g2p_draft_publish.models.draft_records.G2PDraftRecord.env") as mock_env:
            mock_env.ref.return_value.id = 123
            result = record.action_change_state()
            self.assertEqual(result["res_model"], "change.state.wizard")
            self.assertEqual(result["view_id"], 123)

    def test_action_publish_individual(self):
        record = self.Draft.create({"given_name": "Alice", "family_name": "Smith", "is_group": False})

        with patch(
            "odoo.addons.g2p_draft_publish.models.draft_records.G2PDraftRecord._notify_validators"
        ), patch(
            "odoo.addons.base.models.res_partner.Partner.create",
            return_value=self.env["res.partner"].browse(),
        ), patch(
            "odoo.addons.g2p_draft_publish.models.draft_records.G2PDraftRecord._prepare_valid_data"
        ) as mock_prepare:
            mock_prepare.side_effect = lambda valid_data, fields_metadata, partner_data: valid_data.update(
                {"given_name": "Alice", "family_name": "Smith", "is_group": False}
            )

            record.action_publish()
            self.assertEqual(record.state, "published")

    def test_action_publish_with_invalid_data_raises(self):
        """Ensure ValueError is raised when no valid data is found."""
        record = self.Draft.create(
            {
                "given_name": "Invalid",
                "is_group": False,
            }
        )

        with patch(
            "odoo.addons.g2p_draft_publish.models.draft_records.G2PDraftRecord._prepare_valid_data"
        ) as mock_prepare:
            mock_prepare.side_effect = lambda valid_data, fields_metadata, partner_data: None

            with self.assertRaises(ValueError) as cm:
                record.action_publish()

            self.assertEqual(str(cm.exception), "No valid data found to create a partner record.")

    def test_action_reject(self):
        record = self.Draft.create({"name": "RejectMe"})
        result = record.action_reject()
        self.assertEqual(result["res_model"], "g2p.reject.wizard")
        self.assertEqual(result["target"], "new")

    def test_process_json_data(self):
        """Ensure _process_json_data returns correct formatted values."""
        draft = self.Draft.create(
            {
                "name": "Dummy",
                "is_group": False,
            }
        )

        draft.partner_data = json.dumps(
            {
                "name": "Jane Smith",
                "gender": "female",
                "birthdate": "2000-01-01",
                "phone_number_ids": [(0, 0, {"phone_no": "1111111111"})],
                "tags_ids": [(6, 0, [1, 2])],
            }
        )

        result, additional_g2p_info = draft._process_json_data(json.loads(draft.partner_data))

        self.assertEqual(result["default_name"], "Jane Smith")
        self.assertEqual(result["default_birthdate"], date(2000, 1, 1))
        self.assertEqual(
            [tuple(item) for item in result["default_phone_number_ids"]], [(0, 0, {"phone_no": "1111111111"})]
        )
        self.assertEqual(additional_g2p_info["gender"], "female")

    def test_action_publish_group_with_individuals(self):
        GroupMembership = self.env["g2p.group.membership"].sudo()

        individual1 = self.Draft.create(
            {
                "given_name": "Anna",
                "family_name": "Bell",
                "gender": "female",
                "is_group": False,
            }
        )
        individual2 = self.Draft.create(
            {
                "given_name": "Carl",
                "family_name": "Doe",
                "gender": "male",
                "is_group": False,
            }
        )

        group = self.Draft.create(
            {
                "name": "Test Group",
                "is_group": True,
                "group_member_ids_json": [individual1.id, individual2.id],
            }
        )

        partner = group.action_publish()

        group = self.Draft.browse(group.id)
        individual1 = self.Draft.browse(individual1.id)
        individual2 = self.Draft.browse(individual2.id)

        self.assertEqual(group.state, "published")
        self.assertEqual(individual1.state, "published")
        self.assertEqual(individual2.state, "published")
        self.assertTrue(partner.is_group)
        self.assertEqual(partner.name, "TEST GROUP")

        memberships = GroupMembership.search([("group", "=", partner.id)])
        self.assertEqual(len(memberships), 2)
        self.assertIn(memberships[0].individual.name, ["ANNA BELL", "CARL DOE"])
        self.assertIn(memberships[1].individual.name, ["ANNA BELL", "CARL DOE"])

    def test_action_submit_group_with_members_and_activities(self):
        # Create an internal approver user and assign to approver group
        approver_user = self.env["res.users"].create(
            {
                "name": "Approver",
                "login": "approver@test.com",
                "email": "approver@test.com",
                "groups_id": [(6, 0, [self.env.ref("g2p_draft_publish.group_int_approver").id])],
            }
        )

        individual1 = self.Draft.create(
            {
                "given_name": "Member1",
                "family_name": "Test",
                "gender": "male",
                "is_group": False,
            }
        )
        individual2 = self.Draft.create(
            {
                "given_name": "Member2",
                "family_name": "Test",
                "gender": "female",
                "is_group": False,
            }
        )

        group = self.Draft.create(
            {
                "name": "Group One",
                "is_group": True,
                "group_member_ids_json": [individual1.id, individual2.id],
            }
        )

        self.env["mail.activity"].create(
            {
                "res_model_id": self.env["ir.model"]._get("g2p.draft.record").id,
                "res_id": group.id,
                "user_id": self.env.user.id,
                "activity_type_id": self.env.ref("mail.mail_activity_data_todo").id,
                "summary": "Initial Activity",
            }
        )

        group.action_submit()

        group = self.env["g2p.draft.record"].browse(group.id)
        individual1 = self.env["g2p.draft.record"].browse(individual1.id)
        individual2 = self.env["g2p.draft.record"].browse(individual2.id)

        self.assertEqual(group.state, "submitted")
        self.assertEqual(individual1.state, "submitted")
        self.assertEqual(individual2.state, "submitted")

        partner_data = json.loads(group.partner_data)
        self.assertEqual(partner_data.get("imported_record_state"), "submitted")

        done_activities = self.env["mail.activity"].search(
            [
                ("res_model", "=", "g2p.draft.record"),
                ("res_id", "=", group.id),
                ("user_id", "=", self.env.user.id),
                ("activity_type_id", "=", self.env.ref("mail.mail_activity_data_todo").id),
            ]
        )
        self.assertTrue(all(a.date_done for a in done_activities))

        approver_activities = self.env["mail.activity"].search(
            [
                ("res_model", "=", "g2p.draft.record"),
                ("res_id", "=", group.id),
                ("user_id", "=", approver_user.id),
            ]
        )
        self.assertTrue(approver_activities)
        self.assertEqual(approver_activities[0].summary, "Record Submitted For Approval")

    def test_prepare_field_value(self):
        draft = self.Draft.create({"name": "Field Test", "is_group": False})

        self.assertEqual(draft._prepare_field_value("float", 5, {}), 5.0)

        self.assertEqual(draft._prepare_field_value("char", "hello", {}), "hello")
        self.assertEqual(draft._prepare_field_value("text", "world", {}), "world")

        self.assertTrue(draft._prepare_field_value("boolean", True, {}))

        self.assertEqual(draft._prepare_field_value("selection", "opt1", {}), "opt1")

        self.assertEqual(draft._prepare_field_value("many2one", 10, {}), 10)

        self.assertEqual(draft._prepare_field_value("many2many", [(6, 0, [1, 2])], {}), [(6, 0, [1, 2])])

        input_value = [(0, 0, {"name": "child"})]
        expected_output = [(0, 0, {"name": "child"})]
        self.assertEqual(draft._prepare_field_value("one2many", input_value, {}), expected_output)

        today = date.today()
        now = datetime.now()
        self.assertEqual(draft._prepare_field_value("date", today, {}), today)
        self.assertEqual(draft._prepare_field_value("datetime", now, {}), now)

        self.assertEqual(draft._prepare_field_value("unknown_type", "val", {}), "val")

    def test_return_wizard_with_context_valid_data(self):
        draft = self.Draft.create(
            {
                "name": "Wizard Test",
                "is_group": False,
            }
        )

        draft.partner_data = json.dumps(
            {
                "name": "Jane",
                "gender": "female",
                "birthdate": "1990-01-01",
                "phone_number_ids": [(0, 0, {"phone_no": "9876543210"})],
                "tags_ids": [(6, 0, [1, 2])],
            }
        )

        view_id = self.env.ref("base.view_partner_form").id
        result = draft._return_wizard_with_context(view_id)

        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "res.partner")
        self.assertEqual(result["view_id"], view_id)
        self.assertTrue("default_name" in result["context"])
        self.assertEqual(result["context"]["default_is_group"], False)

    def test_return_wizard_with_context_invalid_json(self):
        draft = self.Draft.create(
            {
                "name": "Bad JSON",
                "is_group": False,
            }
        )

        draft.partner_data = "invalid json"

        with self.assertRaises(UserError, msg="Invalid JSON data in partner_data."):
            draft._return_wizard_with_context(self.env.ref("base.view_partner_form").id)

    def test_return_wizard_with_context_no_data(self):
        draft = self.Draft.create(
            {
                "name": "No Data",
                "is_group": False,
            }
        )
        draft.partner_data = None

        with self.assertRaises(UserError, msg="No partner data available."):
            draft._return_wizard_with_context(self.env.ref("base.view_partner_form").id)

    def test_action_open_individual_wizard(self):
        draft = self.Draft.create(
            {
                "name": "Test",
                "is_group": False,
            }
        )
        draft.partner_data = json.dumps({"name": "Test", "is_group": False})
        result = draft.action_open_individual_wizard()
        self.assertEqual(result["res_model"], "res.partner")
        self.assertTrue(result["context"]["default_is_group"] is False)

    def test_action_open_group_wizard(self):
        draft = self.Draft.create(
            {
                "name": "Group Test",
                "is_group": True,
            }
        )
        draft.partner_data = json.dumps({"name": "Group Test", "is_group": True})
        result = draft.action_open_group_wizard()
        self.assertEqual(result["res_model"], "res.partner")
        self.assertTrue(result["context"]["default_is_group"] is True)

    def test_action_open_individual_wizard_view_only(self):
        draft = self.Draft.create(
            {
                "name": "Jane View Only",
                "is_group": False,
            }
        )
        draft.partner_data = json.dumps({"name": "Jane View Only", "is_group": False})
        result = draft.action_open_individual_wizard_view_only()
        self.assertEqual(result["res_model"], "res.partner")
        self.assertIn("default_is_group", result["context"])
        self.assertFalse(result["context"]["default_is_group"])

    def test_action_open_group_wizard_view_only(self):
        draft = self.Draft.create(
            {
                "name": "Group View Only",
                "is_group": True,
            }
        )
        draft.partner_data = json.dumps({"name": "Group View Only", "is_group": True})
        result = draft.action_open_group_wizard_view_only()
        self.assertEqual(result["res_model"], "res.partner")
        self.assertIn("default_is_group", result["context"])
        self.assertTrue(result["context"]["default_is_group"])

    def test_notify_validators_only_exclusive_users(self):
        validator_user = self.env["res.users"].create(
            {
                "name": "Validator",
                "login": "validator@example.com",
                "email": "validator@example.com",
                "groups_id": [(6, 0, [self.env.ref("g2p_draft_publish.group_int_validator").id])],
            }
        )

        validator_user.groups_id = [(3, self.env.ref("g2p_draft_publish.group_int_admin").id)]
        validator_user.groups_id = [(3, self.env.ref("g2p_draft_publish.group_int_approver").id)]

        draft = self.Draft.create({"name": "NotifyTest"})

        draft.message_partner_ids = [(4, validator_user.partner_id.id)]

        with patch.object(type(draft), "message_post", autospec=True) as mock_msg_post:
            draft._notify_validators()

            mock_msg_post.assert_called_once()
            partner_ids = mock_msg_post.call_args.kwargs["partner_ids"]
            self.assertIn(validator_user.partner_id.id, partner_ids)


class TestWebSaveResPartner(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Partner = self.env["res.partner"]
        self.DraftRecord = self.env["g2p.draft.record"]

    def test_action_save_to_draft_json_update(self):
        """Ensure action_save_to_draft updates the partner_data JSON correctly."""

        draft = self.DraftRecord.create(
            {
                "given_name": "John",
                "family_name": "Doe",
                "gender": "male",
            }
        )

        vals = {
            "given_name": "Johnathan",
            "family_name": "Doe",
            "addl_name": "X",
            "gender": "male",
            "tags_ids": [(6, 0, [])],
        }

        context = {
            "draft": True,
            "active_model": "g2p.draft.record",
            "active_id": draft.id,
        }

        partner = self.Partner.create({"name": "DRAFT TEMP"})
        partner.with_context(**context).web_save(vals, {})

        draft = self.env["g2p.draft.record"].browse(draft.id)

        data = json.loads(draft.partner_data)

        self.assertEqual(data["given_name"], "Johnathan")
        self.assertEqual(data["family_name"], "Doe")
        self.assertEqual(data["addl_name"], "X")
        self.assertEqual(data["is_group"], False)
        self.assertEqual(data["is_registrant"], True)
        self.assertEqual(data["db_import"], "yes")
        self.assertEqual(data["name"], "JOHNATHAN DOE X")

    def test_group_draft_record_save(self):
        """Test saving data for group-type draft record"""

        draft = self.DraftRecord.create(
            {
                "name": "My Group",
                "is_group": True,
            }
        )

        vals = {
            "name": "Updated Group Name",
            "phone": "9999999999",
        }

        context = {
            "draft": True,
            "active_model": "g2p.draft.record",
            "active_id": draft.id,
        }

        partner = self.Partner.create({"name": "DRAFT TEMP"})
        partner.with_context(**context).web_save(vals, {})

        draft = self.env["g2p.draft.record"].browse(draft.id)
        data = json.loads(draft.partner_data)

        self.assertEqual(data["name"], "Updated Group Name")
        self.assertEqual(data["is_group"], True)
        self.assertEqual(data["db_import"], "yes")
        self.assertEqual(data["is_registrant"], True)

    def test_res_partner_action_submit(self):
        draft = self.env["g2p.draft.record"].create(
            {
                "given_name": "Alice",
                "family_name": "Smith",
                "gender": "female",
                "phone": "9876543210",
            }
        )

        partner = (
            self.env["res.partner"]
            .with_context(
                active_model="g2p.draft.record",
                active_id=draft.id,
            )
            .create({"name": "Temp"})
        )

        partner.action_submit()

        draft = self.env["g2p.draft.record"].browse(draft.id)
        self.assertEqual(draft.state, "submitted")

    def test_res_partner_action_submit_already_submitted(self):
        draft = self.env["g2p.draft.record"].create(
            {
                "given_name": "Bob",
                "family_name": "Test",
                "gender": "male",
                "phone": "1234567890",
                "state": "submitted",
            }
        )

        partner = (
            self.env["res.partner"]
            .with_context(
                active_model="g2p.draft.record",
                active_id=draft.id,
            )
            .create({"name": "Temp"})
        )

        with self.assertRaises(ValidationError):
            partner.action_submit()

    def test_res_partner_action_publish(self):
        draft = self.env["g2p.draft.record"].create(
            {
                "given_name": "John",
                "family_name": "Doe",
                "gender": "male",
                "phone": "1234567890",
            }
        )

        partner = (
            self.env["res.partner"]
            .with_context(
                active_model="g2p.draft.record",
                active_id=draft.id,
            )
            .create({"name": "Temp"})
        )

        partner.action_submit()
        partner.action_publish()

        draft = self.env["g2p.draft.record"].browse(draft.id)
        self.assertEqual(draft.state, "published")

    def test_res_partner_action_publish_already_published(self):
        draft = self.env["g2p.draft.record"].create(
            {
                "given_name": "Jane",
                "family_name": "Doe",
                "gender": "female",
                "phone": "5551234567",
                "state": "published",
            }
        )

        partner = (
            self.env["res.partner"]
            .with_context(
                active_model="g2p.draft.record",
                active_id=draft.id,
            )
            .create({"name": "Temp"})
        )

        with self.assertRaises(ValidationError):
            partner.action_publish()
