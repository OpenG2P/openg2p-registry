# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

from unittest.mock import patch

from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestG2PSocialRegistryModel(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create or get gender record
        Gender = cls.env["gender.type"]
        cls.gender = Gender.search([("code", "=", "male")], limit=1)
        if not cls.gender:
            cls.gender = Gender.create(
                {
                    "value": "Male",
                    "code": "male",
                }
            )

        # Mock S3 backend to avoid AWS configuration issues during tests
        with patch("odoo.addons.storage_backend_s3.components.s3_adapter.S3StorageAdapter._get_bucket"):
            # Create a shared test user
            cls.test_user = cls.env["res.users"].create(
                {
                    "name": "Test Social User",
                    "login": "test_social_user",
                    "email": "test_social@example.com",
                }
            )
            cls.test_user.write({"password": "SocialTest123!"})

            # Make the user a supplier with supplier_rank > 0 so portal check passes
            cls.test_user.partner_id.write({"supplier_rank": 1})

        # Shared payload data
        cls.shared_data = {
            "birthdate": "1990-01-01",
            "gender": cls.gender.value,
            "email": "demo@example.com",
            "address": "Village 1",
            "occupation": "Farmer",
            "income": "30000",
            "education_level": "bachelors",
            "employment_status": "self_employed",
            "marital_status": "single",
            # Social group data
            "num_preg_lact_women": "2",
            "num_malnourished_children": "1",
            "num_disabled": "1",
            "type_of_disability": "visual_impairment",
            "caste_ethnic_group": "bantu",
            "belong_to_protected_groups": "no",
            "other_vulnerable_status": "no",
            "income_sources": "agriculture",
            "annual_income": "above_10000",
            "owns_two_wheeler": "yes",
            "owns_three_wheeler": "no",
            "owns_four_wheeler": "no",
            "owns_cart": "no",
            "land_ownership": "yes",
            "type_of_land_owned": "agricultural",
            "land_size": "2.5",
            "owns_house": "yes",
            "owns_livestock": "yes",
        }

    def test_group_create_submit(self):
        self.authenticate("test_social_user", "SocialTest123!")

        data = self.shared_data.copy()
        data["name"] = "Shared Test Group"

        response = self.url_open("/portal/registration/group/create/submit", data=data)
        self.assertIn(response.status_code, (200, 303))
        self.assertTrue(response.url.endswith("/portal/registration/group"))

        group = self.env["res.partner"].search([("name", "=", "Shared Test Group")], limit=1)
        self.assertTrue(group.exists())
        self.assertEqual(group.num_disabled, 1)

    def test_individual_create_submit(self):
        self.authenticate("test_social_user", "SocialTest123!")

        data = self.shared_data.copy()
        data.update(
            {"given_name": "Amit", "addl_name": "K", "family_name": "Verma", "email": "amit@example.com"}
        )

        response = self.url_open("/portal/registration/individual/create/submit", data=data)
        self.assertIn(response.status_code, (200, 303))
        self.assertTrue(response.url.endswith("/portal/registration/individual"))

        person = self.env["res.partner"].search([("email", "=", "amit@example.com")], limit=1)
        self.assertTrue(person.exists())
        self.assertEqual(person.income, 30000.0)

    def test_individual_update_submit(self):
        self.authenticate("test_social_user", "SocialTest123!")

        # Create individual once and update
        with patch("odoo.addons.storage_backend_s3.components.s3_adapter.S3StorageAdapter._get_bucket"):
            partner = self.env["res.partner"].create(
                {
                    "name": "Verma, Amit",
                    "given_name": "Amit",
                    "family_name": "Verma",
                    "is_group": False,
                    "is_registrant": True,
                    "user_id": self.test_user.id,
                }
            )

        data = self.shared_data.copy()
        data.update(
            {
                "group_id": partner.id,
                "given_name": "Amit",
                "addl_name": "K",
                "family_name": "Verma",
                "email": "updated_amit@example.com",
                "income": "50000",
            }
        )

        response = self.url_open("/portal/registration/individual/update/submit", data=data)
        self.assertIn(response.status_code, (200, 303))

        updated = self.env["res.partner"].browse(partner.id)
        self.assertEqual(updated.email, "updated_amit@example.com")
        self.assertEqual(updated.income, 50000.0)
