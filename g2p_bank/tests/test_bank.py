import logging
import random

from schwifty import IBAN

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class BankTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(BankTest, cls).setUpClass()

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

    def test_01_add_bank(self):
        # Search for Sample Bank or Create if None
        bank = self.env["res.bank"].search([("name", "=", "Sample Bank")])
        bank_id = None
        if bank:
            bank_id = bank[0]
        else:
            vals = {"name": "Sample Bank", "bic": "1010101010"}
            bank_id = self.env["res.bank"].create(vals)

        vals = []

        # Generate Number Account Number
        random_acc = str(random.randint(1, 9999999999))

        # Compute Expected IBAN
        expected_iban = IBAN.generate(
            bank_id.country.code,
            bank_code=bank_id.bic,
            account_code=random_acc,
        )

        val = {
            "bank_id": bank_id.id,
            "acc_number": random_acc,
        }
        vals.append([0, 0, val])

        # Save Random Account Number to Bank Details
        self.registrant_1.write({"bank_ids": vals})

        self.assertEqual(self.registrant_1.bank_ids[0].iban, expected_iban)
