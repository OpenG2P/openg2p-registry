from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestResPartnerDashboard(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner_model = self.env["res.partner"]

    def test_get_dashboard_data_success(self):
        """Test successful data retrieval and processing."""
        company_id = self.env.company.id

        # Mock data that matches the expected database structure
        mock_result = (
            {"total_individuals": 100, "total_groups": 20},
            {"Male": 70, "Female": 50},
            {
                "below_18": 10,
                "18_to_30": 30,
                "31_to_40": 25,
                "41_to_50": 15,
                "above_50": 20,
            },
        )

        with patch.object(self.env, "cr") as mock_cr:
            mock_cr.fetchone.side_effect = [None, mock_result]
            result = self.partner_model.get_dashboard_data()
            self.assertEqual(mock_cr.execute.call_count, 2)
            mock_cr.execute.assert_any_call(
                """
            SELECT total_registrants, gender_spec, age_distribution
            FROM g2p_registry_dashboard_data
            WHERE company_id = %s
        """,
                (company_id,),
            )

            # Verify the returned data structure and values
            self.assertEqual(result["total_individuals"], 100)
            self.assertEqual(result["total_groups"], 20)
            self.assertEqual(result["gender_distribution"], {"Male": 70, "Female": 50})
            self.assertEqual(
                result["age_distribution"],
                {
                    "Below 18": 10,
                    "18 to 30": 30,
                    "31 to 40": 25,
                    "41 to 50": 15,
                    "Above 50": 20,
                },
            )
