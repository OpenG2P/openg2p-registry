from unittest.mock import MagicMock, patch

from odoo.exceptions import MissingError
from odoo.tests.common import TransactionCase


class TestDashboardMaterializedView(TransactionCase):
    def setUp(self):
        super().setUp()
        self.cron_model = self.env["ir.cron"]

    def test_successful_refresh_of_views(self):
        """All materialized views exist and refresh works without error."""
        mock_cr = MagicMock()
        mock_cr.fetchall.return_value = [("g2p_dummy",)]

        cron = self.cron_model
        cron.env.cr = mock_cr

        with patch.object(cron.env, "cr", mock_cr):
            cron._refresh_dashboard_materialized_view()

        # Check that SELECT + REFRESH was called 4 times each
        select_count = sum(1 for call in mock_cr.execute.call_args_list if "FROM pg_matviews" in call[0][0])
        refresh_count = sum(
            1 for call in mock_cr.execute.call_args_list if "REFRESH MATERIALIZED VIEW" in call[0][0]
        )

        self.assertEqual(select_count, 4)
        self.assertEqual(refresh_count, 4)

    def test_refresh_view_failure_raises_missing_error(self):
        """If REFRESH statement fails, raise MissingError and log the error."""
        mock_cr = MagicMock()
        mock_cr.fetchall.return_value = [("g2p_dummy",)]

        def mock_execute(sql, *args, **kwargs):
            if "REFRESH MATERIALIZED VIEW" in sql:
                raise Exception("Simulated SQL failure")

        mock_cr.execute.side_effect = mock_execute

        cron = self.cron_model
        cron.env.cr = mock_cr

        with patch.object(cron.env, "cr", mock_cr), self.assertRaises(MissingError) as context:
            cron._refresh_dashboard_materialized_view()

        self.assertIn("Failed to refresh", str(context.exception))

    def test_missing_view_raises_missing_error(self):
        """If a view doesn't exist, raise MissingError."""
        mock_cr = MagicMock()
        mock_cr.fetchall.return_value = []

        cron = self.cron_model
        cron.env.cr = mock_cr

        with self.assertLogs("odoo.addons.g2p_registry_dashboard.models.cron", level="ERROR") as log:
            with self.assertRaises(MissingError):
                cron._refresh_dashboard_materialized_view()

            self.assertTrue(any("does not exist" in message for message in log.output))
