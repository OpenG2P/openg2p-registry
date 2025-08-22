from unittest.mock import MagicMock

from odoo.exceptions import MissingError
from odoo.tests.common import TransactionCase

from odoo.addons.g2p_registry_dashboard import drop_materialized_view, init_materialized_view


class TestMaterializedViewInit(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env_mock = MagicMock()
        self.cr_mock = MagicMock()
        self.env_mock.cr = self.cr_mock

    def test_init_materialized_view_creates_missing_views(self):
        # Simulate that no views exist initially
        self.cr_mock.fetchall.return_value = []

        init_materialized_view(self.env_mock)

        # 5 SELECT + 4 CREATE MATERIALIZED VIEWs = 5 execute calls
        self.assertGreaterEqual(self.cr_mock.execute.call_count, 5)

    def test_init_materialized_view_handles_existing_views(self):
        # Simulate that only some materialized views already exist
        self.cr_mock.fetchall.return_value = [
            ("g2p_gender_count_view",),
            ("g2p_total_registrants_view",),
        ]

        init_materialized_view(self.env_mock)

        # Collect all SQL statements executed
        executed_sqls = [args[0] for args, _ in self.cr_mock.execute.call_args_list]

        # Assert gender view was NOT recreated
        self.assertFalse(
            any("CREATE MATERIALIZED VIEW g2p_gender_count_view" in sql for sql in executed_sqls)
        )

        # Assert age_distribution_view and dashboard_data were created
        self.assertTrue(
            any("CREATE MATERIALIZED VIEW g2p_age_distribution_view" in sql for sql in executed_sqls)
        )
        self.assertTrue(
            any("CREATE MATERIALIZED VIEW g2p_registry_dashboard_data" in sql for sql in executed_sqls)
        )

    def test_init_materialized_view_fails(self):
        # Simulate exception
        self.cr_mock.fetchall.side_effect = Exception("DB failed")

        with self.assertRaises(MissingError) as context:
            init_materialized_view(self.env_mock)

        self.assertIn("Failed to create", str(context.exception))


class TestMaterializedViewDrop(TransactionCase):
    def setUp(self):
        super().setUp()
        self.env_mock = MagicMock()
        self.cr_mock = MagicMock()
        self.env_mock.cr = self.cr_mock

    def test_drop_materialized_view_success(self):
        drop_materialized_view(self.env_mock)

        # Should call DROP 4 times
        self.assertEqual(self.cr_mock.execute.call_count, 4)
        self.assertTrue(
            all(
                "DROP MATERIALIZED VIEW IF EXISTS" in call[0][0]
                for call in self.cr_mock.execute.call_args_list
            )
        )

    def test_drop_materialized_view_failure(self):
        self.cr_mock.execute.side_effect = Exception("Drop failed")

        with self.assertRaises(MissingError) as context:
            drop_materialized_view(self.env_mock)

        self.assertIn("Failed to drop", str(context.exception))
