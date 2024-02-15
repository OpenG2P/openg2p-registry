from odoo.tests.common import TransactionCase


class TestG2PDistrict(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        existing_country = cls.env["res.country"].search([("code", "=", "TC")])
        if not existing_country:
            cls.country = cls.env["res.country"].create(
                {"name": "Test Country", "code": "TC"}
            )
        else:
            cls.country = existing_country

        cls.state_model = cls.env["res.country.state"]
        cls.state = cls.state_model.create(
            {"name": "Test State", "code": "TS", "country_id": cls.country.id}
        )
        cls.district_model = cls.env["g2p.district"]

    def test_01_create_district(self):
        district_data = {"name": "Test District"}
        district = self.district_model.create(district_data)
        self.assertEqual(district.name, "Test District", "District name is incorrect")

    def test_02_create_district_with_state(self):
        state_data = {
            "name": "Test State",
            "country_id": self.env.ref("base.in").id,
            "code": "UniqueCode",
        }
        state = self.state_model.create(state_data)

        district_data = {"name": "Test District", "state_id": state.id}
        district = self.district_model.create(district_data)

        self.assertEqual(district.name, "Test District", "District name is incorrect")
        self.assertEqual(district.state_id, state, "District state is incorrect")
