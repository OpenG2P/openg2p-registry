import logging

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

    def test_01_add_phone_check_sanitized(self):
        Phone_Number = "09123456789"
        vals = {"phone_no": Phone_Number}
        self.group_1.write({"phone_number_ids": [(0, 0, vals)]})

        message = "Phone Creation FAILED (EXPECTED %s but RESULT is %s)" % (
            Phone_Number,
            self.group_1.phone_number_ids[0].phone_no,
        )
        self.assertEqual(
            self.group_1.phone_number_ids[0].phone_no, Phone_Number, message
        )

        Expected_Sanitized = "+639123456789"
        message = "Phone Sanitation FAILED (EXPECTED %s but RESULT is %s)" % (
            Expected_Sanitized,
            self.group_1.phone_number_ids[0].phone_sanitized,
        )
        self.assertEqual(
            self.group_1.phone_number_ids[0].phone_sanitized,
            Expected_Sanitized,
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
        Expected_Value = "112233445566778899"
        message = "ID Creation FAILED (EXPECTED %s but RESULT is %s)" % (
            Expected_Value,
            self.group_1.reg_ids[0].value,
        )
        self.assertEqual(self.group_1.reg_ids[0].value, Expected_Value, message)

    def test_03_add_relationship(self):
        rel_type = self.env["g2p.relationship"].create(
            {
                "name": "Friend",
                "name_inverse": "Friend",
            }
        )
        vals2 = {"registrant2": self.group_2.id, "relation": rel_type.id}

        self.group_1.write({"related_2_ids": [(0, 0, vals2)]})

        message = "ID Creation FAILED (EXPECTED %s but RESULT is %s)" % (
            self.group_2.id,
            self.group_1.related_2_ids[0].registrant2.id,
        )
        self.assertEqual(
            self.group_1.related_2_ids[0].registrant2.id, self.group_2.id, message
        )
