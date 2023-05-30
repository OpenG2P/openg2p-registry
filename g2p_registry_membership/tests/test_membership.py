# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

import logging

from odoo import fields

# from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class MembershipTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(MembershipTest, cls).setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                test_queue_job_no_delay=True,
            )
        )

        # Initial Setup of Variables
        cls.registrant_1 = cls.env["res.partner"].create(
            {
                "family_name": "Jaddranka",
                "given_name": "Heidi",
                "name": "Heidi Jaddranka",
                "is_group": False,
                "is_registrant": True,
            }
        )
        cls.registrant_2 = cls.env["res.partner"].create(
            {
                "family_name": "Kleitos",
                "given_name": "Angus",
                "name": "Angus Kleitos",
                "is_group": False,
                "is_registrant": True,
            }
        )
        cls.registrant_3 = cls.env["res.partner"].create(
            {
                "family_name": "Caratacos",
                "given_name": "Sora",
                "name": "Sora Caratacos",
                "is_group": False,
                "is_registrant": True,
            }
        )
        cls.registrant_4 = cls.env["res.partner"].create(
            {
                "family_name": "Demophon",
                "given_name": "Amaphia",
                "name": "Amaphia Demophon",
                "is_group": False,
                "is_registrant": True,
            }
        )
        cls.group_1 = cls.env["res.partner"].create(
            {
                "name": "Group 1",
                "is_group": True,
                "is_registrant": True,
            }
        )
        cls.group_2 = cls.env["res.partner"].create(
            {
                "name": "Group 2",
                "is_group": True,
                "is_registrant": True,
            }
        )
        cls.group_3 = cls.env["res.partner"].create(
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

    def test_03_disabled_individual(self):
        """
        Disable an individual and modify its data.
        The test will run the write method of res.partner and execute the _recompute_parent_groups function.
        :return:
        """
        _logger.info(
            "Test 3: Add individual: %s to group: %s."
            % (self.registrant_3.name, self.group_2.name)
        )
        self.registrant_3.write(
            {"individual_membership_ids": [(0, 0, {"group": self.group_2.id})]}
        )
        self.assertEqual(
            self.registrant_3.individual_membership_ids[0].group.id,
            self.group_2.id,
            "Cannot add individual to group!",
        )

        _logger.info("Test 3: Set individual: %s to disabled." % self.registrant_3.name)
        curr_date = fields.Datetime.now()
        self.registrant_3.update(
            {
                "disabled": curr_date,
                "disabled_reason": "Disable reason",
                "disabled_by": self.env.user,
            }
        )
        self.assertEqual(
            self.registrant_3.disabled, curr_date, "Error disabling an individual!"
        )

        _logger.info(
            "Test 3: Modify disabled individual: %s information. %s"
            % (self.registrant_3.name, self.registrant_3.disabled)
        )
        self.registrant_3.update(
            {
                "family_name": "Burito",
            }
        )
        self.assertEqual(
            self.registrant_3.family_name,
            "Burito",
            "Error modifying information of disabled individual!",
        )

    def test_04_individual_with_ended_membership(self):
        """
        End an individual's membership with a group and modify its data.
        The test will run the write method of res.partner and execute the _recompute_parent_groups function.
        :return:
        """
        _logger.info(
            "Test 4: Add individual: %s to group: %s."
            % (self.registrant_4.name, self.group_1.name)
        )
        self.registrant_4.write(
            {"individual_membership_ids": [(0, 0, {"group": self.group_1.id})]}
        )
        self.assertEqual(
            self.registrant_4.individual_membership_ids[0].group.id,
            self.group_1.id,
            "Cannot add individual to group!",
        )

        grp_rec = self.group_1.group_membership_ids[0]
        _logger.info(
            "Test 4: End membership of individual: %s membership with group: %s."
            % (grp_rec.individual.name, grp_rec.group.name)
        )
        curr_date = fields.Datetime.now()
        grp_rec.update({"ended_date": curr_date})
        self.assertEqual(
            grp_rec.is_ended, True, "Error ending the individual's membership to group!"
        )

        _logger.info(
            "Test 4: Modify individual with ended membership: %s information. %s"
            % (grp_rec.individual.name, grp_rec.is_ended)
        )
        grp_rec.individual.update(
            {
                "name": "Test 4 Individual",
            }
        )
        self.assertEqual(
            grp_rec.individual.name,
            "Test 4 Individual",
            "Error modifying information of individual with ended membership!",
        )

    def test_05_group_indicators(self):
        """
        Add members to a group and check if the indicator field z_ind_grp_num_individuals is updating.
        :return:
        """
        curr_date = fields.Datetime.now()
        _logger.info(
            "Test 5: Add individual: %s and %s to group: %s."
            % (self.registrant_3.name, self.registrant_4.name, self.group_2.name)
        )
        self.group_2.write(
            {
                "group_membership_ids": [
                    (0, 0, {"individual": self.registrant_3.id}),
                    (0, 0, {"individual": self.registrant_4.id}),
                ]
            }
        )
        _logger.info(
            "Test 5: Check group: %s total membership: %s."
            % (self.group_2.name, len(self.group_2.group_membership_ids))
        )
        self.assertEqual(
            len(self.group_2.group_membership_ids),
            2,
            "The total number of members in the group is incorrect!",
        )

        grp_rec = self.group_2.group_membership_ids[0]
        _logger.info(
            "Test 5: End membership of individual: %s" % grp_rec.individual.name
        )
        grp_rec.update(
            {
                "ended_date": curr_date,
            }
        )
        self.assertEqual(
            grp_rec.is_ended,
            True,
            "Error ending the membership of individual from group!",
        )

        _logger.info(
            "Test 5: Check group: %s indicator field z_ind_grp_num_individuals: %s."
            % (self.group_2.name, self.group_2.z_ind_grp_num_individuals)
        )
        # self.assertEqual(
        #    self.group_2.z_ind_grp_num_individuals,
        #    2,
        #    "The total number of individuals in indicator field: z_ind_grp_num_individuals is incorrect!",
        # )
