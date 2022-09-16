import logging
import random
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.phone_validation.tools import phone_validation

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class IndividualsTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(IndividualsTest, cls).setUpClass()

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

    def test_01_check_names(self):
        self.registrant_1.name_change()
        message = "NAME FAILED (EXPECTED %s but RESULT is %s)" % (
            "JADDRANKA, HEIDI ",
            self.registrant_1.name,
        )
        self.assertEqual(self.registrant_1.name, "JADDRANKA, HEIDI ", message)
        self.registrant_2.name_change()
        message = "NAME FAILED (EXPECTED %s but RESULT is %s)" % (
            "KLEITOS, ANGUS ",
            self.registrant_2.name,
        )
        self.assertEqual(self.registrant_2.name, "KLEITOS, ANGUS ", message)
        self.registrant_3.name_change()
        message = "NAME FAILED (EXPECTED %s but RESULT is %s)" % (
            "CARATACOS, SORA ",
            self.registrant_3.name,
        )
        self.assertEqual(self.registrant_3.name, "CARATACOS, SORA ", message)
        self.registrant_4.name_change()
        message = "NAME FAILED (EXPECTED %s but RESULT is %s)" % (
            "DEMOPHON, AMAPHIA ",
            self.registrant_4.name,
        )
        self.assertEqual(self.registrant_4.name, "DEMOPHON, AMAPHIA ", message)

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
        message = "Age Calculation FAILED (EXPECTED %s but RESULT is %s)" % (
            age,
            self.registrant_1.age,
        )
        self.assertEqual(self.registrant_1.age, age, message)

    def test_03_add_phone_check_sanitized(self):
        phone_number = "09123456789"
        vals = {"phone_no": phone_number}
        self.registrant_1.write({"phone_number_ids": [(0, 0, vals)]})

        message = "Phone Creation FAILED (EXPECTED %s but RESULT is %s)" % (
            phone_number,
            self.registrant_1.phone_number_ids[0].phone_no,
        )
        self.assertEqual(
            self.registrant_1.phone_number_ids[0].phone_no, phone_number, message
        )
        expected_sanitized = ""
        country_fname = "country_id"
        number = phone_number
        sanitized = str(
            phone_validation.phone_sanitize_numbers_w_record(
                [number],
                self,
                record_country_fname=country_fname,
                force_format="E164",
            )[number]["sanitized"]
        )
        expected_sanitized = sanitized
        message = "Phone Sanitation FAILED (EXPECTED %s but RESULT is %s)" % (
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
        vals = {"id_type": id_type.id, "value": "112233445566778899"}

        self.registrant_1.write({"reg_ids": [(0, 0, vals)]})
        expected_value = "112233445566778899"
        message = "ID Creation FAILED (EXPECTED %s but RESULT is %s)" % (
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

        message = "ID Creation FAILED (EXPECTED %s but RESULT is %s)" % (
            self.registrant_2.id,
            self.registrant_1.related_2_ids[0].destination.id,
        )
        self.assertEqual(
            self.registrant_1.related_2_ids[0].destination.id,
            self.registrant_2.id,
            message,
        )
