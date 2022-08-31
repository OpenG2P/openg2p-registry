# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

from .common import JobCommonCase


class TestJobsOnComputeFieldMethod(JobCommonCase):
    """Test Job on Compute Fields"""

    def test_01_create_registrants(self):
        # Initial Setup of Variables
        self.registrant_1 = self.env["res.partner"].create(
            {
                "family_name": "Jaddranka",
                "given_name": "Heidi",
                "name": "Heidi Jaddranka",
                "is_group": False,
                "is_registrant": True,
            }
        )
        self.registrant_2 = self.env["res.partner"].create(
            {
                "family_name": "Kleitos",
                "given_name": "Angus",
                "name": "Angus Kleitos",
                "is_group": False,
                "is_registrant": True,
            }
        )
        self.registrant_3 = self.env["res.partner"].create(
            {
                "family_name": "Caratacos",
                "given_name": "Sora",
                "name": "Sora Caratacos",
                "is_group": False,
                "is_registrant": True,
            }
        )
        self.registrant_4 = self.env["res.partner"].create(
            {
                "family_name": "Demophon",
                "given_name": "Amaphia",
                "name": "Amaphia Demophon",
                "is_group": False,
                "is_registrant": True,
            }
        )
        self.group_1 = self.env["res.partner"].create(
            {
                "name": "Group 1",
                "is_group": True,
                "is_registrant": True,
            }
        )
        self.group_2 = self.env["res.partner"].create(
            {
                "name": "Group 2",
                "is_group": True,
                "is_registrant": True,
            }
        )
        self.group_3 = self.env["res.partner"].create(
            {
                "name": "Group 3",
                "is_group": True,
                "is_registrant": True,
            }
        )

    def test_01_add_members(self):
        self.group_1.write(
            {"group_membership_ids": [(0, 0, {"individual": self.registrant_1.id})]}
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
        self.registrant_2.write(
            {"individual_membership_ids": [(0, 0, {"group": self.group_2.id})]}
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
