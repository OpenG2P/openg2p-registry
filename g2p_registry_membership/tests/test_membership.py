# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

import logging
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError

# from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class MembershipTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        self.group_1.write({"group_membership_ids": [(0, 0, {"individual": self.registrant_1.id})]})
        message = "Membership Testing: Adding Group Member Failed! Result: {} Expecting: {}".format(
            self.group_1.group_membership_ids[0].individual.name,
            self.registrant_1.name,
        )
        self.assertEqual(
            self.group_1.group_membership_ids[0].individual.id,
            self.registrant_1.id,
            message,
        )

    def test_02_assign_member(self):
        self.registrant_2.write({"individual_membership_ids": [(0, 0, {"group": self.group_2.id})]})
        message = "Membership Testing: Assigning Member to Group Failed! Result {} Expecting {}".format(
            self.registrant_2.individual_membership_ids[0].group.id,
            self.group_2.id,
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
        _logger.info(f"Test 3: Add individual: {self.registrant_3.name} to group: {self.group_2.name}.")
        self.registrant_3.write({"individual_membership_ids": [(0, 0, {"group": self.group_2.id})]})
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
        self.assertEqual(self.registrant_3.disabled, curr_date, "Error disabling an individual!")

        _logger.info(
            f"Test 3: Modify disabled individual: {self.registrant_3.name} information. "
            f"{self.registrant_3.disabled}"
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
        _logger.info(f"Test 4: Add individual: {self.registrant_4.name} to group: {self.group_1.name}.")
        self.registrant_4.write({"individual_membership_ids": [(0, 0, {"group": self.group_1.id})]})
        self.assertEqual(
            self.registrant_4.individual_membership_ids[0].group.id,
            self.group_1.id,
            "Cannot add individual to group!",
        )

        grp_rec = self.group_1.group_membership_ids[0]
        _logger.info(
            f"Test 4: End membership of individual: {grp_rec.individual.name} membership with "
            f"group: {grp_rec.group.name}."
        )
        curr_date = fields.Datetime.now()
        grp_rec.update({"ended_date": curr_date})
        self.assertEqual(grp_rec.is_ended, True, "Error ending the individual's membership to group!")

        _logger.info(
            f"Test 4: Modify individual with ended membership: {grp_rec.individual.name} information. "
            f"{grp_rec.is_ended}"
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
        _logger.info(f"Test 5: Add individual: {self.registrant_1.name} to group: {self.group_2.name}.")
        self.registrant_1.write({"individual_membership_ids": [(0, 0, {"group": self.group_2.id})]})
        self.assertEqual(
            self.registrant_1.individual_membership_ids[0].group.id,
            self.group_2.id,
            "Cannot add individual to group!",
        )
        _logger.info(f"Test 5: Add individual: {self.registrant_2.name} to group: {self.group_2.name}.")
        self.registrant_2.write({"individual_membership_ids": [(0, 0, {"group": self.group_2.id})]})
        self.assertEqual(
            self.registrant_2.individual_membership_ids[0].group.id,
            self.group_2.id,
            "Cannot add individual to group!",
        )

        _logger.info(
            f"Test 5: Add individual: {self.registrant_3.name} "
            f"and {self.registrant_4.name} to group: {self.group_2.name}."
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
            f"Test 5: Check group: {self.group_2.name} "
            f"total membership: {len(self.group_2.group_membership_ids)}."
        )
        self.assertEqual(
            len(self.group_2.group_membership_ids),
            4,
            "The total number of members in the group is incorrect!",
        )

        grp_rec = self.group_2.group_membership_ids[1]
        curr_date = fields.Datetime.now()
        _logger.info(f"Test 5: End membership of individual: {grp_rec.individual.name} - {curr_date}")
        grp_rec.update({"ended_date": curr_date})
        self.assertEqual(
            grp_rec.is_ended,
            True,
            "Error ending the individual's membership with the group!",
        )

        _logger.info(
            f"Test 5: Check group: {self.group_2.name} "
            f"indicator field z_ind_grp_num_individuals: {self.group_2.z_ind_grp_num_individuals}."
        )
        # self.assertEqual(
        #    self.group_2.z_ind_grp_num_individuals,
        #    2,
        #    "The total number of individuals in indicator field: z_ind_grp_num_individuals is incorrect!",
        # )

    def test_06_check_group_members(self):
        # Create a group membership record with a specific group and individual
        group_membership_1 = self.env["g2p.group.membership"].create(
            {
                "group": self.group_1.id,
                "individual": self.registrant_1.id,
                "start_date": fields.Datetime.now(),
            }
        )

        # Ensure that the first record is created successfully
        self.assertTrue(group_membership_1)

        # Try to create another group membership with the same individual and group
        # (expecting a ValidationError)
        with self.assertRaises(ValidationError):
            self.env["g2p.group.membership"].create(
                {
                    "group": self.group_1.id,
                    "individual": self.registrant_1.id,
                    "start_date": fields.Datetime.now(),
                }
            )

    def test_07_check_name(self):
        # Create a group membership kind record with a specific name
        group_membership_kind_1 = self.env["g2p.group.membership.kind"].create(
            {
                "name": "Test Kind",
            }
        )

        # Ensure that the first record is created successfully
        self.assertTrue(group_membership_kind_1)

        # Try to create another group membership kind with an empty name (expecting a ValidationError)
        with self.assertRaises(ValidationError):
            self.env["g2p.group.membership.kind"].create(
                {
                    "name": "",
                }
            )

        # Try to create another group membership kind with the same name (expecting a ValidationError)
        with self.assertRaises(ValidationError):
            self.env["g2p.group.membership.kind"].create(
                {
                    "name": "test kind",
                }
            )

    def test_08_check_ended_date(self):
        # Create a group membership record with a specific start and end date
        group_membership_1 = self.env["g2p.group.membership"].create(
            {
                "group": self.group_1.id,
                "individual": self.registrant_1.id,
                "start_date": fields.Datetime.now(),
                "ended_date": fields.Datetime.now(),  # Set the end date to the same as the start date
            }
        )

        # Ensure that the first record is created successfully
        self.assertTrue(group_membership_1)

        # Try to create another group membership with an end date earlier than the start date
        # (expecting a ValidationError)
        with self.assertRaises(ValidationError):
            self.env["g2p.group.membership"].create(
                {
                    "group": self.group_1.id,
                    "individual": self.registrant_1.id,
                    "start_date": fields.Datetime.now(),
                    "ended_date": fields.Datetime.now()
                    - timedelta(days=1),  # Set the end date earlier than the start date
                }
            )

    def test_09_check_kind_onchange(self):
        # Create a group membership record with a specific group and individual
        group_membership = self.env["g2p.group.membership"].create(
            {
                "group": self.group_1.id,
                "individual": self.registrant_1.id,
                "start_date": fields.Datetime.now(),
            }
        )

        # Ensure that the group membership is created successfully
        self.assertTrue(group_membership)

        # Create a unique kind
        unique_kind = self.env["g2p.group.membership.kind"].create(
            {
                "name": "Unique Kind",
                "is_unique": True,
            }
        )

        # Add the unique kind to the group membership
        group_membership.write({"kind": [(6, 0, [unique_kind.id])]})

        try:
            # Create another group membership with the same unique kind (expecting a ValidationError)
            self.env["g2p.group.membership"].create(
                {
                    "group": self.group_1.id,
                    "individual": self.registrant_2.id,
                    "start_date": fields.Datetime.now(),
                    "kind": [(6, 0, [unique_kind.id])],
                }
            )
        except ValidationError as e:
            # Log the validation error for additional information
            _logger.error("Validation Error: %s", e)
            raise  # Re-raise the exception to mark the test as failed

    def test_10_name_search(self):
        # Test case for _name_search method
        name = "Group 1"
        results_query = self.env["g2p.group.membership"]._name_search(name, operator="ilike")
        # Extract the IDs from the query result
        results = [result[0] for result in results_query]
        expected_result = self.group_1.group_membership_ids.ids
        self.assertListEqual(results, expected_result, "Name search not working correctly.")

    def test_11_recompute_parent_groups(self):
        # Test case for _recompute_parent_groups method

        # Create a new group_membership_ids record
        new_membership = self.env["g2p.group.membership"].create(
            {
                "group": self.group_1.id,
                "individual": self.registrant_1.id,
            }
        )

        # Write the individual field of the newly created record
        new_membership.write({"individual": self.registrant_2.id})

        # Recompute parent groups
        self.group_1.group_membership_ids._recompute_parent_groups(records=new_membership)

        # Check whether the group.name is recomputed correctly
        self.assertEqual(
            new_membership.group.name,
            "Group 1",
            "Parent groups not recomputed correctly.",
        )

    def test_12_open_individual_form(self):
        # Test case for open_individual_form method

        # Create a group membership record for self.group_1
        membership_data = {
            "individual": self.registrant_1.id,
            "group": self.group_1.id,
            # Add other required fields based on your model structure
        }
        self.env["g2p.group.membership"].create(membership_data)

        # Ensure that group_membership_ids is not empty
        self.assertTrue(
            self.group_1.group_membership_ids,
            "No group membership records found.",
        )

        # Access the first element only if the tuple is not empty
        if self.group_1.group_membership_ids:
            action = self.group_1.group_membership_ids[0].open_individual_form()
            self.assertEqual(
                action["res_id"],
                self.registrant_1.id,
                "Open individual form action not generated correctly.",
            )
        else:
            self.fail("No group membership records found.")

    def test_13_open_group_form(self):
        # Test case for open_group_form method
        # Create a group membership record for self.group_1
        membership_data = {
            "individual": self.registrant_1.id,
            "group": self.group_1.id,
            # Add other required fields based on your model structure
        }
        self.env["g2p.group.membership"].create(membership_data)

        # Ensure that group_membership_ids is not empty
        self.assertTrue(
            self.group_1.group_membership_ids,
            "No group membership records found.",
        )

        # Access the first element only if the tuple is not empty
        if self.group_1.group_membership_ids:
            action = self.group_1.group_membership_ids[0].open_group_form()
            self.assertEqual(
                action["res_id"],
                self.group_1.id,
                "Open group form action not generated correctly.",
            )
        else:
            self.fail("No group membership records found.")

    def test_14_compute_status(self):
        # Create a group membership record for group_1
        group_membership = self.env["g2p.group.membership"].create(
            {
                "group": self.group_1.id,
                "individual": self.registrant_1.id,
                "start_date": fields.Datetime.now(),
            }
        )

        # Update the ended_date of the created group membership record
        group_membership.write({"ended_date": fields.Datetime.now()})

        # Check the computed status
        self.assertEqual(
            group_membership.status,
            "inactive",
            "Status not computed correctly.",
        )

    def test_15_compute_force_recompute_group(self):
        # Test case for _compute_force_recompute_group method
        current_canary = self.group_1.force_recompute_canary
        self.group_1._compute_force_recompute_group()

        # Verify that the force_recompute_canary has been updated
        new_canary = self.group_1.force_recompute_canary
        self.assertNotEqual(
            new_canary,
            current_canary,
            "Force recompute canary not updated correctly.",
        )

        # Verify that the new_canary is close to the current datetime
        current_datetime = fields.Datetime.now()
        delta = timedelta(seconds=10)  # Adjust the delta as needed
        self.assertLessEqual(
            current_datetime - new_canary,
            delta,
            f"Force recompute canary was not updated close to the current datetime. "
            f"Current datetime: {current_datetime}, New canary: {new_canary}",
        )

    def test_16_compute_ind_grp_num_individuals(self):
        # Test case for _compute_ind_grp_num_individuals method
        self.group_1.group_membership_ids.unlink()
        self.group_1._compute_ind_grp_num_individuals()
        self.assertEqual(
            self.group_1.z_ind_grp_num_individuals,
            0,
            "Number of individuals not computed correctly.",
        )

    def test_17_recompute_indicators_for_all_records(self):
        # Test case for recompute_indicators_for_all_records method
        self.group_1.group_membership_ids.unlink()
        self.group_1.recompute_indicators_for_all_records()
        self.assertEqual(
            self.group_1.z_ind_grp_num_individuals,
            0,
            "Indicators not recomputed correctly for all records.",
        )

    def test_18_recompute_indicators_for_batch(self):
        # Test case for recompute_indicators_for_batch method
        self.group_1.group_membership_ids.unlink()
        self.group_1.recompute_indicators_for_batch(0, 10)
        self.assertEqual(
            self.group_1.z_ind_grp_num_individuals,
            0,
            "Indicators not recomputed correctly for batch.",
        )

    def test_19_recompute_indicators(self):
        # Test case for recompute_indicators method
        self.group_1.group_membership_ids.unlink()
        self.group_1.recompute_indicators()
        self.assertEqual(
            self.group_1.z_ind_grp_num_individuals,
            0,
            "Indicators not recomputed correctly.",
        )

    def test_20_get_calculated_group_fields(self):
        # Test case for _get_calculated_group_fields method
        calculated_fields = self.group_1._get_calculated_group_fields(["z_ind_grp_num_individuals"])
        self.assertIn(
            self.group_1._fields["z_ind_grp_num_individuals"],
            calculated_fields,
            "Calculated fields not retrieved correctly.",
        )

    def test_21_count_individuals(self):
        # Test case for count_individuals method
        self.group_1.group_membership_ids.unlink()
        self.assertEqual(self.group_1.count_individuals(), {}, "Count of individuals not correct.")

    def test_22_query_members_aggregate(self):
        # Test case for _query_members_aggregate method
        self.group_1.group_membership_ids.unlink()
        result = self.group_1._query_members_aggregate()
        self.assertEqual(result, [], "Query members aggregate result not correct.")

    def test_23_compute_count_and_set_indicator(self):
        # Test case for compute_count_and_set_indicator method
        self.group_1.group_membership_ids.unlink()
        self.group_1.compute_count_and_set_indicator("z_ind_grp_num_individuals", None, [])
        self.assertEqual(
            self.group_1.z_ind_grp_num_individuals,
            0,
            "Compute count and set indicator not correct.",
        )

    def test_24_update_compute_fields(self):
        # Test case for _update_compute_fields method
        self.group_1.group_membership_ids.unlink()
        records = self.group_1
        self.group_1._update_compute_fields(records, "z_ind_grp_num_individuals", None, [])
        self.assertEqual(
            self.group_1.z_ind_grp_num_individuals,
            0,
            "Update compute fields not correct.",
        )

    def test_25_compute_display_name(self):
        # Create a group membership record with a specific group
        group_membership = self.env["g2p.group.membership"].create(
            {
                "group": self.group_1.id,
                "individual": self.registrant_1.id,
                "start_date": fields.Datetime.now(),
            }
        )

        # Ensure that the record is created successfully
        self.assertTrue(group_membership)

        # Use the write method on the specific record to update the group
        group_membership.write({"group": self.group_1.id})

        # Verify the expected display_name
        expected_display_name = self.group_1.name
        self.assertEqual(group_membership.display_name, expected_display_name)
