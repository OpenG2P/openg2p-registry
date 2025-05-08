from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestRegistrant(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create test config
        cls.config = cls.env["g2p.datashare.config"].create(
            {
                "name": "Test Config",
                "host": "localhost",
                "port": 5672,
                "username": "guest",
                "password": "guest",
                "vhost": "/",
                "exchange": "test_exchange",
                "routing_key": "test_routing_key",
                "transform_data_jq": "{id, name}",
                "active": True,
            }
        )

    def test_01_create_registrant(self):
        """Test creating a registrant and verify push"""
        with patch(
            "odoo.addons.g2p_registry_datashare.models.datashare_config.G2PDatashareConfig.publish"
        ) as mock_publish:
            # Create a registrant
            registrant = self.env["res.partner"].create(
                {
                    "name": "Test Registrant",
                    "is_registrant": True,
                    "is_group": False,
                    "email": "test@example.com",
                }
            )

            # Verify the record was created
            self.assertTrue(registrant)
            self.assertTrue(registrant.is_registrant)
            self.assertFalse(registrant.is_group)

            # Verify publish was called
            mock_publish.assert_called_once()
            published_data = mock_publish.call_args[0][0]
            self.assertEqual(published_data["name"], "Test Registrant")

    def test_02_update_registrant(self):
        """Test updating a registrant and verify push"""
        with patch(
            "odoo.addons.g2p_registry_datashare.models.datashare_config.G2PDatashareConfig.publish"
        ) as mock_publish:
            # Create a registrant
            registrant = self.env["res.partner"].create(
                {
                    "name": "Test Registrant",
                    "is_registrant": True,
                    "is_group": False,
                }
            )

            # Update the registrant
            registrant.write({"name": "Updated Registrant"})

            # Verify publish was called
            self.assertEqual(mock_publish.call_count, 2)  # Once for create, once for update
            published_data = mock_publish.call_args[0][0]
            self.assertEqual(published_data["name"], "Updated Registrant")

    def test_03_group_registrant(self):
        """Test that group registrants are not pushed"""
        with patch(
            "odoo.addons.g2p_registry_datashare.models.datashare_config.G2PDatashareConfig.publish"
        ) as mock_publish:
            # Create a group registrant
            self.env["res.partner"].create(
                {
                    "name": "Test Group",
                    "is_registrant": True,
                    "is_group": True,
                }
            )

            # Verify publish was not called
            mock_publish.assert_not_called()

    def test_04_non_registrant(self):
        """Test that non-registrants are not pushed"""
        with patch(
            "odoo.addons.g2p_registry_datashare.models.datashare_config.G2PDatashareConfig.publish"
        ) as mock_publish:
            # Create a non-registrant partner
            self.env["res.partner"].create(
                {
                    "name": "Test Partner",
                    "is_registrant": False,
                    "is_group": False,
                }
            )

            # Verify publish was not called
            mock_publish.assert_not_called()

    def test_05_bulk_create_registrants(self):
        """Test bulk creation of registrants"""
        with patch(
            "odoo.addons.g2p_registry_datashare.models.datashare_config.G2PDatashareConfig.publish"
        ) as mock_publish:
            # Create multiple registrants
            self.env["res.partner"].create(
                [
                    {
                        "name": "Registrant 1",
                        "is_registrant": True,
                        "is_group": False,
                    },
                    {
                        "name": "Registrant 2",
                        "is_registrant": True,
                        "is_group": False,
                    },
                ]
            )

            # Verify publish was called for each registrant
            self.assertEqual(mock_publish.call_count, 2)

    def test_06_failed_transformation(self):
        """Test handling of failed JQ transformation"""
        # Set invalid JQ expression
        self.config.transform_data_jq = "invalid jq"

        with patch(
            "odoo.addons.g2p_registry_datashare.models.datashare_config.G2PDatashareConfig.publish"
        ) as mock_publish:
            # Create a registrant
            self.env["res.partner"].create(
                {
                    "name": "Test Registrant",
                    "is_registrant": True,
                    "is_group": False,
                }
            )

            # Verify publish was not called due to failed transformation
            mock_publish.assert_not_called()
