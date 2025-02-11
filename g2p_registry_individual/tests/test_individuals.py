import logging
import random
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class IndividualsTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Initial Setup of Variables
        cls.registrant_1 = cls.env["res.partner"].create(
            {
                "name": "Heidi Jaddranka",
                "family_name": "Jaddranka",
                "given_name": "Heidi",
                "is_group": False,
                "is_registrant": True,
            }
        )
        cls.registrant_2 = cls.env["res.partner"].create(
            {
                "name": "Angus Kleitos",
                "family_name": "Kleitos",
                "given_name": "Angus",
                "is_group": False,
                "is_registrant": True,
            }
        )
        cls.registrant_3 = cls.env["res.partner"].create(
            {
                "name": "Sora Caratacos",
                "family_name": "Caratacos",
                "given_name": "Sora",
                "is_group": False,
                "is_registrant": True,
            }
        )
        cls.registrant_4 = cls.env["res.partner"].create(
            {
                "name": "Amaphia Demophon",
                "family_name": "Demophon",
                "given_name": "Amaphia",
                "is_group": False,
                "is_registrant": True,
            }
        )
        cls.registrant_no_given_name = cls.env["res.partner"].create(
            {
                "name": "Josephine Demophon",
                "family_name": "Demophon",
                "given_name": "",
                "addl_name": "Josephine",
                "is_group": False,
                "is_registrant": True,
            }
        )
        cls.registrant_no_addl_name = cls.env["res.partner"].create(
            {
                "name": "Amaphia Demophon",
                "family_name": "Demophon",
                "given_name": "Amaphia",
                "addl_name": "",
                "is_group": False,
                "is_registrant": True,
            }
        )
        cls.registrant_all_names = cls.env["res.partner"].create(
            {
                "name": "Amaphia Jospehine Demophon",
                "family_name": "Demophon",
                "given_name": "Amaphia",
                "addl_name": "Josephine",
                "is_group": False,
                "is_registrant": True,
            }
        )
        cls.registrant_no_family_name = cls.env["res.partner"].create(
            {
                "name": "Amaphia Jospehine",
                "family_name": "",
                "given_name": "Amaphia",
                "addl_name": "Josephine",
                "is_group": False,
                "is_registrant": True,
            }
        )

    def test_01_check_name_change(self):
        self.registrant_no_family_name.name_change()
        self.assertEqual(self.registrant_no_family_name.name, "AMAPHIA JOSEPHINE")
        self.registrant_all_names.name_change()
        self.assertEqual(self.registrant_all_names.name, "DEMOPHON, AMAPHIA JOSEPHINE")
        self.registrant_no_addl_name.name_change()
        self.assertEqual(self.registrant_no_addl_name.name, "DEMOPHON, AMAPHIA")
        self.registrant_no_given_name.name_change()
        self.assertEqual(self.registrant_no_given_name.name, "DEMOPHON, JOSEPHINE")

    def test_02_age_calculation(self):
        start_date = date(2000, 1, 1)
        end_date = date(2022, 12, 30)
        time_between_dates = end_date - start_date
        days_between_dates = time_between_dates.days
        random_number_of_days = random.randrange(days_between_dates)
        random_date = start_date + timedelta(days=random_number_of_days)

        now = date.today()
        if random_date:
            dob = random_date
            delta = relativedelta(now, dob)
            # years_months_days = str(delta.years) +"y "+ str(delta.months) +"m "+ str(delta.days)+"d"
            years_months_days = str(delta.years)
        else:
            years_months_days = "No Birthdate!"

        age = years_months_days
        self.registrant_1.birthdate = random_date
        message = f"Age Calculation FAILED (EXPECTED {age} but RESULT is {self.registrant_1.age})"
        self.assertEqual(self.registrant_1.age, age, message)

    def test_03_add_phone_check_sanitized(self):
        phone_number = "09123456789"
        vals = {"phone_no": phone_number}
        self.registrant_1.write({"phone_number_ids": [(0, 0, vals)]})

        message = "Phone Creation FAILED (EXPECTED {} but RESULT is {})".format(
            phone_number,
            self.registrant_1.phone_number_ids[0].phone_no,
        )
        self.assertEqual(self.registrant_1.phone_number_ids[0].phone_no, phone_number, message)
        expected_sanitized = ""
        country_fname = self.registrant_1.phone_number_ids[0].country_id
        number = phone_number
        sanitized = str(
            self.env.user._phone_format(
                number=number,
                country=country_fname,
                force_format="E164",
            )
        )
        expected_sanitized = sanitized
        message = "Phone Sanitation FAILED (EXPECTED {} but RESULT is {})".format(
            expected_sanitized,
            self.registrant_1.phone_number_ids[0].phone_sanitized,
        )
        self.assertEqual(
            self.registrant_1.phone_number_ids[0].phone_sanitized,
            expected_sanitized,
            message,
        )

    def test_04_add_id(self):
        id_type = self.env["g2p.id.type"].create(
            {
                "name": "Testing ID Type",
            }
        )
        vals = {
            "id_type": id_type.id,
            "value": "112233445566778899",
            "status": "valid",
            "description": "Due to API",
        }

        self.registrant_1.write({"reg_ids": [(0, 0, vals)]})
        expected_value = "112233445566778899"
        message = "ID Creation FAILED (EXPECTED {} but RESULT is {})".format(
            expected_value,
            self.registrant_1.reg_ids[0].value,
        )
        self.assertEqual(self.registrant_1.reg_ids[0].value, expected_value, message)

    def test_05_add_relationship(self):
        rel_type = self.env["g2p.relationship"].create(
            {
                "name": "Friend",
                "name_inverse": "Friend",
            }
        )
        vals2 = {"destination": self.registrant_2.id, "relation": rel_type.id}

        self.registrant_1.write({"related_2_ids": [(0, 0, vals2)]})

        message = "ID Creation FAILED (EXPECTED {} but RESULT is {})".format(
            self.registrant_2.id,
            self.registrant_1.related_2_ids[0].destination.id,
        )
        self.assertEqual(
            self.registrant_1.related_2_ids[0].destination.id,
            self.registrant_2.id,
            message,
        )
