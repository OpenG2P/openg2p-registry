import logging
from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class RegistrantTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Initial Setup of Variables
        cls.registrant = cls.env["res.partner"].create(
            {
                "name": "John Doe",
                "is_group": False,
                "is_registrant": True,
            }
        )

    def test_01_enable_registrant(self):
        # Disable registrant first
        self.registrant.write(
            {
                "disabled": date.today(),
                "disabled_by": self.env.user.id,
                "disabled_reason": "Test",
            }
        )

        # Enable registrant
        self.registrant.enable_registrant()

        # Check if registrant is enabled
        self.assertFalse(self.registrant.disabled)
        self.assertFalse(self.registrant.disabled_by)
        self.assertFalse(self.registrant.disabled_reason)

    # def test_02_onchange_negative_restrict(self):
    #     # Set income to a negative value
    #     self.registrant.write({"income": -100})

    #     # Check if any warning is present
    #     with self.assertWarns(UserWarning, msg="No warning message found"):
    #         self.registrant._onchange_negative_restrict()

    #     print("current income value:", self.registrant.income)

    def test_03_check_registration_date(self):
        self.registrant.registration_date = date(2022, 1, 1)
        self.registrant.birthdate = date(2031, 1, 1)

        with self.assertRaises(ValidationError) as context:
            self.registrant._check_registration_date()
        self.assertEqual(
            str(context.exception),
            "Registration date must be less than the current date.",
            "Validation error message.",
        )

        with self.assertRaises(ValidationError) as e:
            self.registrant._check_registration_date()
        self.assertEqual(
            str(e.exception),
            "Registration date must be less than the birth date.",
            "Validation error message.",
        )

    def test_04_check_phone_number_validation(self):
        # Add a phone number with an invalid format
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.registrant.write(
                {"phone_number_ids": [(0, 0, {"phone_no": "invalid"})]}
            )

        # Set an invalid phone number
        invalid_phone = "12345"
        with self.assertRaisesRegex(Exception, "Invalid phone number!"):
            self.registrant.write(
                {"phone_number_ids": [(0, 0, {"phone_no": invalid_phone})]}
            )

        # Set a valid phone number
        valid_phone = "1234567890"
        self.registrant.write({"phone_number_ids": [(0, 0, {"phone_no": valid_phone})]})

        # Check if the phone number is set successfully
        self.assertEqual(self.registrant.phone_number_ids[0].phone_no, valid_phone)

    def test_05_onchange_phone_validation(self):
        with self.assertRaises(ValidationError):
            self.registrant._onchange_phone_validation()
        # Set an invalid phone number using 'phone' field
        invalid_phone = "12345"
        with self.assertRaisesRegex(Exception, "Invalid phone number!"):
            self.registrant.write({"phone": invalid_phone})

        # Set a valid phone number using 'phone' field
        valid_phone = "1234567890"
        self.registrant.write({"phone": valid_phone})

        # Check if the 'phone' field is set successfully
        self.assertEqual(self.registrant.phone, valid_phone)

    def test_06_onchange_mobile_validation(self):
        # Set an invalid phone number using 'mobile' field
        invalid_mobile = "9876"
        with self.assertRaisesRegex(Exception, "Invalid mobile number!"):
            self.registrant.write({"mobile": invalid_mobile})

        # Set a valid phone number using 'mobile' field
        valid_mobile = "9876543210"
        self.registrant.write({"mobile": valid_mobile})

        # Check if the 'mobile' field is set successfully
        self.assertEqual(self.registrant.mobile, valid_mobile)
