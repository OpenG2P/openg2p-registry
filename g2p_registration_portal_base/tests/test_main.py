import json

from odoo.tests.common import HttpCase
from odoo.tools import mute_logger


class TestG2PregistrationPortalBase(HttpCase):
    def setUp(self):
        super().setUp()

        self.test_user = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_user",
                "email": "test@example.com",
            }
        )

        self.test_user.partner_id.write(
            {
                "supplier_rank": 1,
                "is_registrant": True,
                "is_group": True,
            }
        )

        self.test_user.write({"password": "TestUser1!"})

        self.gender = self.env["gender.type"].create({"value": "Male", "code": "male"})

    def test_group_list(self):
        # Test accessing the group list page
        self.authenticate("test_user", "TestUser1!")

        response = self.url_open("/portal/registration/group")
        self.assertEqual(response.status_code, 200)

    def test_group_create(self):
        # Test accessing the group create page
        self.authenticate("test_user", "TestUser1!")

        response = self.url_open("/portal/registration/group/create/")
        self.assertEqual(response.status_code, 200)

    def test_group_create_submit(self):
        # Test submitting the group creation form.
        self.authenticate("test_user", "TestUser1!")

        response = self.url_open(
            "/portal/registration/group/create/submit",
            data={
                "name": "Test Group",
                "dob": "2023-10-26",
                "gender": self.gender.value,
            },
        )

        self.assertEqual(response.status_code, 200)  # Check for successful redirection

    def test_group_update(self):
        # Test accessing the group update page
        self.authenticate("test_user", "TestUser1!")

        group = self.env["res.partner"].create(
            {
                "name": "Group to Update",
                "is_registrant": True,
                "is_group": True,
            }
        )

        response = self.url_open(f"/portal/registration/group/update/{group.id}")
        self.assertEqual(response.status_code, 200)

    def test_group_update_submit(self):
        # Test submitting the group update form
        self.authenticate("test_user", "TestUser1!")

        group = self.env["res.partner"].create(
            {"name": "Group to Update", "is_registrant": True, "is_group": True, "street": "Old Street"}
        )

        response = self.url_open(
            "/portal/registration/group/update/submit/",
            data={
                "group_id": group.id,
                "street": "New Street",
            },
        )

        self.assertEqual(response.status_code, 200)
        updated_group = self.env["res.partner"].browse(group.id)
        self.assertEqual(updated_group.street, "New Street")

    @mute_logger("odoo.http")
    def test_individual_create(self):
        # Test creating an individual member within a household
        self.authenticate("test_user", "TestUser1!")

        response = self.url_open(
            "/portal/registration/member/create/",
            data={
                "Household_name": "GIVEN ADDL FAMILY",
                "Household_dob": "2023-01-01",
                "Household_gender": self.gender.value,
                "given_name": "Individual",
                "family_name": "One",
                "birthdate": "2024-01-01",
                "gender": self.gender.value,
            },
        )

        self.assertEqual(response.status_code, 200)

        recieved_member = json.loads(response.content)
        self.assertEqual(len(recieved_member["member_list"]), 2, "Incorrect number of members")

    @mute_logger("odoo.http")
    def test_update_member(self):
        # Test accessing the member update page
        self.authenticate("test_user", "TestUser1!")

        member = self.env["res.partner"].create(
            {
                "name": "Member to update",
                "birthdate": "2023-05-05",
                "gender": self.gender.value,
            }
        )
        response = self.url_open("/portal/registration/member/update/", data={"member_id": member.id})

        self.assertEqual(response.status_code, 200)

        received_member = json.loads(response.content)
        self.assertEqual(received_member["id"], member.id)

    @mute_logger("odoo.http")
    def test_update_member_submit(self):
        # Test submitting the member update form
        self.authenticate("test_user", "TestUser1!")

        member = self.env["res.partner"].create(
            {
                "name": "Member to update",
                "birthdate": "2023-05-05",
                "gender": self.gender.value,
            }
        )
        response = self.url_open(
            "/portal/registration/member/update/submit/",
            data={
                "member_id": member.id,
                "given_name": "Updated",
                "family_name": "Member",
                "birthdate": "2023-06-06",
                "gender": self.gender.value,
            },
        )
        self.assertEqual(response.status_code, 200)

        received_member = json.loads(response.content)
        self.assertEqual(len(received_member["member_list"]), 1)
        self.assertEqual(received_member["member_list"][0]["id"], member.id)

    def test_individual_list(self):
        # Test accessing the individual list page
        self.authenticate("test_user", "TestUser1!")

        response = self.url_open("/portal/registration/individual")
        self.assertEqual(response.status_code, 200)

    def test_individual_registrar_create(self):
        # Test accessing the individual creation page as registrar
        self.authenticate("test_user", "TestUser1!")

        response = self.url_open("/portal/registration/individual/create/")
        self.assertEqual(response.status_code, 200)

    def test_individual_create_submit(self):
        # Test submitting the individual creation form
        self.authenticate("test_user", "TestUser1!")

        response = self.url_open(
            "/portal/registration/individual/create/submit",
            data={
                "given_name": "Test",
                "family_name": "Individual",
                "addl_name": "Addl",
                "birthdate": "2023-12-12",
                "gender": self.gender.value,
            },
        )

        self.assertEqual(response.status_code, 200)

    def test_indvidual_update(self):
        # Test accessing the individual update page
        self.authenticate("test_user", "TestUser1!")

        individual = self.env["res.partner"].create(
            {
                "name": "Individual",
                "is_registrant": True,
                "is_group": False,
                "user_id": self.test_user.id,
            }
        )

        response = self.url_open(f"/portal/registration/individual/update/{individual.id}")

        self.assertEqual(response.status_code, 200)

    def test_update_individual_submit(self):
        # Test submitting the individual update form
        self.authenticate("test_user", "TestUser1!")

        individual = self.env["res.partner"].create(
            {
                "name": "Individual",
                "is_registrant": True,
                "is_group": False,
                "user_id": self.test_user.id,
                "birthdate": "2024-01-01",
            }
        )

        response = self.url_open(
            "/portal/registration/individual/update/submit", data={"group_id": individual.id, "birthdate": ""}
        )

        self.assertEqual(response.status_code, 200)

        updated_individual = self.env["res.partner"].browse(individual.id)
        self.assertFalse(updated_individual.birthdate)

    def test_group_create_submit_invalid_field(self):
        # Test group creation with invalid field
        self.authenticate("test_user", "TestUser1!")

        response = self.url_open(
            "/portal/registration/group/create/submit", data={"name": "Test Group", "invalid_field": "value"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.url.endswith("/portal/registration/group"))

    def test_group_submit_invalid_group(self):
        # Test group submission with invalid group_id
        self.authenticate("test_user", "TestUser1!")

        response = self.url_open("/portal/registration/group/update/submit/", data={"group_id": 999999})

        self.assertEqual(response.status_code, 200)

    @mute_logger("odoo.http")
    def test_update_member_invalid_id(self):
        # Test member update with invalid member_id
        self.authenticate("test_user", "TestUser1!")

        response = self.url_open("/portal/registration/member/update/", data={"member_id": 777777})

        self.assertEqual(response.status_code, 200)

    @mute_logger("odoo.http")
    def test_update_member_submit_invalid_id(self):
        # Test member update submission with invalid member_id
        self.authenticate("test_user", "TestUser1!")

        response = self.url_open("/portal/registration/member/update/submit/", data={"member_id": 999999})

        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result, {"error": "Failed to update member details"})
