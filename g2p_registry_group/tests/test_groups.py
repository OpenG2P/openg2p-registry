import logging

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class GroupsTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        _logger.info("Registry: Groups Testing - SETUP INITIALIZED")
        super(GroupsTest, cls).setUpClass()

        # Initial Setup of Variables
        _logger.info("Groups Testing: Creating Group: Group 1")

        cls.group_1 = cls.env["res.partner"].create(
            {
                "name": "Group 1",
                "is_group": True,
            }
        )
        if cls.group_1:
            _logger.info("Groups Testing: Created Group: %s" % cls.group_1.name)
        else:
            _logger.info("Groups Testing: Creation Failed for Group: Group 1")

        _logger.info("Groups Testing: Creating Group: Group 2")

        cls.group_2 = cls.env["res.partner"].create(
            {
                "name": "Group 2",
                "is_group": True,
            }
        )
        if cls.group_2:
            _logger.info("Groups Testing: Created Group: %s" % cls.group_2.name)
        else:
            _logger.info("Groups Testing: Creation Failed for Group: Group 2")

        _logger.info("Groups Testing: Creating Group: Group 3")

        cls.group_3 = cls.env["res.partner"].create(
            {
                "name": "Group 3",
                "is_group": True,
            }
        )
        if cls.group_3:
            _logger.info("Groups Testing: Created Group: %s" % cls.group_3.name)
        else:
            _logger.info("Groups Testing: Creation Failed for Group: Group 3")

    def test_01_add_phone(self):
        _logger.info("Groups Testing: Testing Add Phone")
        Phone_Number = "09123456789"
        _logger.info("Groups Testing: Adding Phone %s" % Phone_Number)
        vals = {"phone_no": Phone_Number}
        self.group_1.write({"phone_number_ids": [(0, 0, vals)]})

        if len(self.group_1.phone_number_ids) > 0:
            _logger.info(
                "Individuals Testing: Added Phone %s, Sanitized: %s"
                % (
                    self.group_1.phone_number_ids[0].phone_no,
                    self.group_1.phone_number_ids[0].phone_sanitized,
                )
            )
        message = (
            "Individuals Testing: Phone Creation FAILED (EXPECTED %s but RESULT is %s)"
            % (
                Phone_Number,
                self.group_1.phone_number_ids[0].phone_no,
            )
        )
        self.assertEqual(
            self.group_1.phone_number_ids[0].phone_no, Phone_Number, message
        )
