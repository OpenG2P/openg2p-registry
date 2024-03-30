import logging

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class GroupsTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(GroupsTest, cls).setUpClass()

        # Initial Setup of Variables
        cls.group_1 = cls.env["res.partner"].create(
            {
                "name": "Group 1",
                "is_registrant": True,
                "is_group": True,
            }
        )
        cls.group_2 = cls.env["res.partner"].create(
            {
                "name": "Group 2",
                "is_registrant": True,
                "is_group": True,
            }
        )
        cls.group_3 = cls.env["res.partner"].create(
            {
                "name": "Group 3",
                "is_registrant": True,
                "is_group": True,
            }
        )
        # New setup for Group Kinds
        cls.group_kind_1 = cls.env["g2p.group.kind"].create(
            {
                "name": "Kind 1",
            }
        )
        cls.group_kind_2 = cls.env["g2p.group.kind"].create(
            {
                "name": "Kind 2",
            }
        )

    def test_01_check_name_constraint(self):
        # Create a group kind with an empty name
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["g2p.group.kind"].create({"name": ""})

        # Create a group kind with a non-unique name
        group_kind_1 = self.env["g2p.group.kind"].create({"name": "Test Kind"})
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["g2p.group.kind"].create({"name": "test kind"})

        # Create a group kind with a unique name
        self.env["g2p.group.kind"].create({"name": "Unique Kind"})

    def test_04_create_group_kind(self):
        # Test case to create a new group kind
        new_group_kind = self.env["g2p.group.kind"].create(
            {
                "name": "New Kind",
            }
        )
        self.assertTrue(new_group_kind)

    def test_05_duplicate_group_kind(self):
        # Test case to ensure that a duplicate group kind cannot be created
        with self.assertRaises(ValidationError):
            self.env["g2p.group.kind"].create(
                {
                    "name": "Kind 1",
                }
            )

    def test_01_add_phone_check_sanitized(self):
        phone_number = "09123456789"
        vals = {"phone_no": phone_number}
        self.group_1.write({"phone_number_ids": [(0, 0, vals)]})

        message = "Phone Creation FAILED (EXPECTED %s but RESULT is %s)" % (
            phone_number,
            self.group_1.phone_number_ids[0].phone_no,
        )
        self.assertEqual(self.group_1.phone_number_ids[0].phone_no, phone_number, message)
        expected_sanitized = ""
        country_fname = self.group_1.phone_number_ids[0].country_id
        number = phone_number
        sanitized = str(
            self.env.user._phone_format(
                number=number,
                country=country_fname,
                force_format="E164",
            )
        )
        expected_sanitized = sanitized
        message = "Phone Sanitation FAILED (EXPECTED %s but RESULT is %s)" % (
            expected_sanitized,
            self.group_1.phone_number_ids[0].phone_sanitized,
        )
        self.assertEqual(
            self.group_1.phone_number_ids[0].phone_sanitized,
            expected_sanitized,
            message,
        )

    def test_02_add_id(self):
        id_type = self.env["g2p.id.type"].create(
            {
                "name": "Testing ID Type",
            }
        )
        vals = {"id_type": id_type.id, "value": "112233445566778899"}

        self.group_1.write({"reg_ids": [(0, 0, vals)]})
        expected_value = "112233445566778899"
        message = "ID Creation FAILED (EXPECTED %s but RESULT is %s)" % (
            expected_value,
            self.group_1.reg_ids[0].value,
        )
        self.assertEqual(self.group_1.reg_ids[0].value, expected_value, message)

    def test_03_add_relationship(self):
        rel_type = self.env["g2p.relationship"].create(
            {
                "name": "Friend",
                "name_inverse": "Friend",
            }
        )
        vals2 = {"destination": self.group_2.id, "relation": rel_type.id}

        self.group_1.write({"related_2_ids": [(0, 0, vals2)]})

        message = "ID Creation FAILED (EXPECTED %s but RESULT is %s)" % (
            self.group_2.id,
            self.group_1.related_2_ids[0].destination.id,
        )
        self.assertEqual(self.group_1.related_2_ids[0].destination.id, self.group_2.id, message)
