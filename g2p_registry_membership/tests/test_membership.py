import logging

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class MembershipTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        _logger.info("Registry: Membership Testing - SETUP INITIALIZED")
        super(MembershipTest, cls).setUpClass()

        # Initial Setup of Variables
        _logger.info("Membership Testing: Creating Registrant: Heidi Jaddranka")
        cls.registrant_1 = cls.env["res.partner"].create(
            {
                "family_name": "Jaddranka",
                "given_name": "Heidi",
                "name": "Heidi Jaddranka",
                "is_group": False,
            }
        )
        if cls.registrant_1:
            _logger.info(
                "Membership Testing: Created Registrant: %s" % cls.registrant_1.name
            )
        else:
            _logger.info(
                "Membership Testing: Creation Failed for Registrant: Heidi Jaddranka"
            )

        _logger.info("Membership Testing: Creating Registrant: Angus Kleitos")
        cls.registrant_2 = cls.env["res.partner"].create(
            {
                "family_name": "Kleitos",
                "given_name": "Angus",
                "name": "Angus Kleitos",
                "is_group": False,
            }
        )
        if cls.registrant_2:
            _logger.info(
                "Membership Testing: Created Registrant: %s" % cls.registrant_2.name
            )
        else:
            _logger.info(
                "Membership Testing: Creation Failed for Registrant: Angus Kleitos"
            )

        _logger.info("Membership Testing: Creating Registrant: Sora Caratacos")
        cls.registrant_3 = cls.env["res.partner"].create(
            {
                "family_name": "Caratacos",
                "given_name": "Sora",
                "name": "Sora Caratacos",
                "is_group": False,
            }
        )
        if cls.registrant_3:
            _logger.info(
                "Membership Testing: Created Registrant: %s" % cls.registrant_3.name
            )
        else:
            _logger.info(
                "Membership Testing: Creation Failed for Registrant: Sora Caratacos"
            )

        _logger.info("Membership Testing: Creating Registrant: Amaphia Demophon")
        cls.registrant_4 = cls.env["res.partner"].create(
            {
                "family_name": "Demophon",
                "given_name": "Amaphia",
                "name": "Amaphia Demophon",
                "is_group": False,
            }
        )
        if cls.registrant_4:
            _logger.info(
                "Membership Testing: Created Registrant: %s" % cls.registrant_4.name
            )
        else:
            _logger.info(
                "Membership Testing: Creation Failed for Registrant: Amaphia Demophon"
            )

        _logger.info("Membership Testing: Creating Group: Group 1")

        cls.group_1 = cls.env["res.partner"].create(
            {
                "name": "Group 1",
                "is_group": True,
            }
        )
        if cls.group_1:
            _logger.info("Membership Testing: Created Group: %s" % cls.group_1.name)
        else:
            _logger.info("Membership Testing: Creation Failed for Group: Group 1")

        _logger.info("Membership Testing: Creating Group: Group 2")

        cls.group_2 = cls.env["res.partner"].create(
            {
                "name": "Group 2",
                "is_group": True,
            }
        )
        if cls.group_2:
            _logger.info("Membership Testing: Created Group: %s" % cls.group_2.name)
        else:
            _logger.info("Membership Testing: Creation Failed for Group: Group 2")

        _logger.info("Membership Testing: Creating Group: Group 3")

        cls.group_3 = cls.env["res.partner"].create(
            {
                "name": "Group 3",
                "is_group": True,
            }
        )
        if cls.group_3:
            _logger.info("Membership Testing: Created Group: %s" % cls.group_3.name)
        else:
            _logger.info("Membership Testing: Creation Failed for Group: Group 3")

    def test_01_add_members(self):
        _logger.info(
            "Membership Testing: Adding Group Member: %s" % self.registrant_1.name
        )
        self.group_1.write(
            {"group_membership_ids": [(0, 0, {"individual": self.registrant_1.id})]}
        )
        if len(self.group_1.group_membership_ids) > 0:
            _logger.info(
                "Membership Testing: Added Group Member: %s"
                % self.group_1.group_membership_ids[0].individual.name
            )
        message = (
            "Membership Testing: Adding Group Member Failed! Result: %s Expecting: %s"
            % (
                self.group_1.group_membership_ids[0].individual.name,
                self.registrant_1.name,
            )
        )
        self.assertEqual(
            self.group_1.group_membership_ids[0].individual.id,
            self.registrant_1.id,
            message,
        )

    def test_02_assign_member(self):
        _logger.info(
            "Membership Testing: Assigning Member to Group: %s" % self.group_2.name
        )
        self.registrant_2.write(
            {"individual_membership_ids": [(0, 0, {"group": self.group_2.id})]}
        )
        if len(self.registrant_2.individual_membership_ids) > 0:
            _logger.info(
                "Membership Testing: Member Assigned to Group: %s"
                % self.registrant_2.individual_membership_ids[0].group.name
            )
        message = (
            "Membership Testing: Assigning Member to Group Failed! Result %s Expecting %s"
            % (
                self.registrant_2.individual_membership_ids[0].group.id,
                self.group_2.id,
            )
        )
        self.assertEqual(
            self.registrant_2.individual_membership_ids[0].group.id,
            self.group_2.id,
            message,
        )
