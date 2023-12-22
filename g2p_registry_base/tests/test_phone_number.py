import logging
from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class TestG2PPhoneNumber(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestG2PPhoneNumber, cls).setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test Registrant", "is_registrant": True}
        )
        country_india = cls.env["res.country"].search([("name", "=", "India")])
        if not country_india:
            country_india = cls.env["res.country"].create(
                {"name": "India", "code": "IN", "phone_code": "91"}
            )

        cls.country_india = country_india
        cls.phone_regex = r"^\+91[1-9]\d{9}$"
        cls.env["ir.config_parameter"].sudo().set_param(
            "g2p_registry.phone_regex", cls.phone_regex
        )

    def test_01_create_phone_number(self):
        phone_number = self.env["g2p.phone.number"].create(
            {
                "partner_id": self.partner.id,
                "phone_no": "+919876543210",
                "country_id": self.country_india.id,
            }
        )
        self.assertEqual(phone_number.phone_sanitized, "+919876543210")

    def test_02_onchange_phone_validation_valid(self):
        phone_number = self.env["g2p.phone.number"].new(
            {
                "phone_no": "+919876543210",
                "country_id": self.country_india.id,
            }
        )
        phone_number._onchange_phone_validation()

    def test_03_onchange_phone_validation_invalid(self):
        phone_number = self.env["g2p.phone.number"].new(
            {
                "phone_no": "invalid",
                "country_id": self.country_india.id,
            }
        )
        with self.assertRaises(ValidationError):
            phone_number._onchange_phone_validation()

    def test_04_disable_enable_phone(self):
        phone_number = self.env["g2p.phone.number"].create(
            {
                "partner_id": self.partner.id,
                "phone_no": "+919876543210",
                "country_id": self.country_india.id,
            }
        )

        self.assertFalse(phone_number.disabled)
        phone_number.disable_phone()
        self.assertTrue(phone_number.disabled)
        phone_number.enable_phone()
        self.assertFalse(phone_number.disabled)

    def test_05_check_date_collected(self):
        today = date.today()
        phone_number = self.env["g2p.phone.number"].create(
            {
                "partner_id": self.partner.id,
                "phone_no": "+919876543210",
                "country_id": self.country_india.id,
                "date_collected": today,
            }
        )
        with self.assertRaises(ValidationError):
            phone_number._check_date_collected()

        future_date = today.replace(year=today.year + 1)
        phone_number.date_collected = future_date
        with self.assertRaises(ValidationError):
            phone_number._check_date_collected()

    def test_06_phone_format(self):
        phone_number = self.env["g2p.phone.number"].create(
            {
                "partner_id": self.partner.id,
                "phone_no": "+919876543210",
                "country_id": self.country_india.id,
            }
        )
        formatted_number = phone_number._phone_format(
            "+919876543210", self.country_india
        )
        self.assertEqual(formatted_number, "+919876543210")

    def test_07_compute_phone_sanitized(self):
        phone_number = self.env["g2p.phone.number"].create(
            {
                "partner_id": self.partner.id,
                "phone_no": "+919876543210",
                "country_id": self.country_india.id,
            }
        )
        phone_number._compute_phone_sanitized()
        self.assertEqual(phone_number.phone_sanitized, "+919876543210")

    def test_08_check_date_collected(self):
        phone_number = self.env["g2p.phone.number"].create(
            {
                "partner_id": self.partner.id,
                "phone_no": "123456789",
                "date_collected": date(2030, 1, 1),
            }
        )
        with self.assertRaises(ValidationError):
            phone_number._check_date_collected()
