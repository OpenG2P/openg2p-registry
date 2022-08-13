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
        _logger.info("Registry: Individuals Testing - SETUP INITIALIZED")
        super(IndividualsTest, cls).setUpClass()

        # Initial Setup of Variables
        _logger.info("Individuals Testing: Creating Registrant: Heidi Jaddranka")
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
                "Individuals Testing: Created Registrant: %s" % cls.registrant_1.name
            )
        else:
            _logger.info(
                "Individuals Testing: Creation Failed for Registrant: Heidi Jaddranka"
            )

        _logger.info("Individuals Testing: Creating Registrant: Angus Kleitos")
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
                "Individuals Testing: Created Registrant: %s" % cls.registrant_2.name
            )
        else:
            _logger.info(
                "Individuals Testing: Creation Failed for Registrant: Angus Kleitos"
            )

        _logger.info("Individuals Testing: Creating Registrant: Sora Caratacos")
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
                "Individuals Testing: Created Registrant: %s" % cls.registrant_3.name
            )
        else:
            _logger.info(
                "Individuals Testing: Creation Failed for Registrant: Sora Caratacos"
            )

        _logger.info("Individuals Testing: Creating Registrant: Amaphia Demophon")
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
                "Individuals Testing: Created Registrant: %s" % cls.registrant_4.name
            )
        else:
            _logger.info(
                "Individuals Testing: Creation Failed for Registrant: Amaphia Demophon"
            )

    def test_01_age_calculation(self):
        _logger.info("Individuals Testing: Testing Age Calculations")

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

        _logger.info(
            "Individuals Testing: Adding Birthdate %s, Expecting Age: %s"
            % (random_date, age)
        )
        self.registrant_1.birthdate = random_date
        if self.registrant_1.birthdate:
            _logger.info(
                "Individuals Testing: Added Birthdate %s, Age: %s"
                % (self.registrant_1.birthdate, self.registrant_1.age)
            )
        message = (
            "Individuals Testing: Age Calculation FAILED (EXPECTED %s but RESULT is %s)"
            % (
                age,
                self.registrant_1.age,
            )
        )
        self.assertEqual(self.registrant_1.age, age, message)
