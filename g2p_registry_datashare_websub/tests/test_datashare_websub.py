from unittest.mock import patch

from odoo.tests import TransactionCase


class TestG2PRegistryDatashareWebsub(TransactionCase):
    """Test suite for G2P Registry Datashare WebSub functionality
    This class tests WebSub event registration, publishing, and data transformation"""

    @patch("requests.post")
    def setUp(self, mock_post):
        """Set up test data with mocked requests

        Args:
            mock_post: Mocked requests.post for HTTP calls

        Creates:
            - WebSub configuration
            - Test group/registrant
        """
        super().setUp()

        # Mock the token response for initial setup
        mock_post.return_value.ok = True
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"access_token": "test_token", "expires_in": 3600}
        mock_post.return_value.text = "hub.mode=accepted"

        # Create test data
        self.websub_config = (
            self.env["g2p.datashare.config.websub"]
            .with_context(test_mode=True)
            .create(
                {
                    "name": "Test WebSub Config",
                    "partner_id": self.env.ref("base.main_partner").id,  # Use existing partner
                    "event_type": "GROUP_CREATED",
                    "websub_base_url": "http://test.websub/hub",
                    "websub_auth_url": "http://test.auth/token",
                    "websub_auth_client_id": "test_client",
                    "websub_auth_client_secret": "test_secret",
                    "transform_data_jq": ".",  # Default passthrough
                    "condition_jq": "true",  # Default always true
                }
            )
        )

        # Create test registrant
        self.test_group = (
            self.env["res.partner"]
            .with_context(test_mode=True)
            .create(
                {
                    "name": "Test Group",
                    "is_group": True,
                    "is_registrant": True,
                }
            )
        )

    @patch("requests.post")
    def test_register_websub_event(self, mock_post):
        """Test WebSub event registration

        Verifies:
            - Event registration API call is made
            - Registration parameters are correct
        """
        # Mock response
        mock_post.return_value.ok = True
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "hub.mode=accepted"
        mock_post.return_value.json.return_value = {"access_token": "test_token", "expires_in": 3600}

        # Reset mock to clear any previous calls
        mock_post.reset_mock()

        # Test registration
        self.websub_config.with_context(test_mode=True).register_websub_event()

        # Verify that the registration call was made
        self.assertTrue(mock_post.called)

        # Optional: Verify call parameters if needed
        call_kwargs = mock_post.call_args[1]
        self.assertIn("data", call_kwargs)
        self.assertEqual(call_kwargs["data"]["hub.mode"], "register")

    @patch("requests.post")
    def test_get_access_token(self, mock_post):
        """Test OAuth token retrieval and caching

        Verifies:
            - New token is retrieved successfully
            - Token is stored in config
            - Expiry is set correctly
            - Token is cached for subsequent calls
        """
        # Reset the token and expiry
        self.websub_config.websub_access_token = False
        self.websub_config.websub_access_token_expiry = False

        # Mock new token response
        mock_post.return_value.ok = True
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"access_token": "new_test_token", "expires_in": 3600}

        # Get new token
        token = self.websub_config.with_context(test_mode=True).get_access_token()

        # Verify the new token
        self.assertEqual(token, "new_test_token")

        # Verify token was stored
        self.assertEqual(self.websub_config.websub_access_token, "new_test_token")

        # Verify expiry was set
        self.assertTrue(self.websub_config.websub_access_token_expiry)

        # Verify the token is cached for subsequent calls
        second_token = self.websub_config.with_context(test_mode=True).get_access_token()
        self.assertEqual(second_token, "new_test_token")

        # Mock post should only be called once as second call uses cached token
        self.assertEqual(mock_post.call_count, 1)

    @patch("requests.post")
    def test_publish_event(self, mock_post):
        """Test event publishing mechanism

        Verifies:
            - Events are published for matching event types
            - Events are not published for non-matching types
            - Correct API calls are made
        """
        # Setup mock response
        mock_post.return_value.ok = True
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "hub.mode=accepted"
        mock_post.return_value.json.return_value = {"access_token": "test_token", "expires_in": 3600}

        # Reset mock call count
        mock_post.reset_mock()

        test_data = {"id": self.test_group.id, "name": "Test Group"}

        # Ensure websub config matches event type
        self.websub_config.write(
            {"event_type": "GROUP_CREATED", "transform_data_jq": ".", "condition_jq": "true"}
        )

        # Test publishing with matching event type
        self.env["g2p.datashare.config.websub"].with_context(test_mode=True).publish_event(
            "GROUP_CREATED", test_data
        )

        # Verify that call was made
        self.assertTrue(mock_post.called)

        # Test with non-matching event type
        mock_post.reset_mock()
        self.env["g2p.datashare.config.websub"].with_context(test_mode=True).publish_event(
            "INDIVIDUAL_CREATED", test_data
        )

        # Verify no calls for non-matching type
        self.assertFalse(mock_post.called)

    @patch("requests.post")
    def test_transform_data_jq(self, mock_post):
        """Test JQ data transformation functionality

        Verifies:
            - Data is correctly transformed using JQ
            - Transformed data structure matches expected format
            - Timestamp handling is correct
        """
        # Setup mock response
        mock_post.return_value.ok = True
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "hub.mode=accepted"
        mock_post.return_value.json.return_value = {"access_token": "test_token", "expires_in": 3600}

        # Create test record
        test_record = self.env["res.partner"].create(
            {
                "name": "Test Transform",
                "is_group": True,
                "is_registrant": True,
            }
        )

        # Use transform
        transform_jq = """{
            ts_ms: .curr_datetime,
            event: .publisher.event_type,
            groupData: .record_data
        }"""

        self.websub_config.write(
            {"transform_data_jq": transform_jq, "event_type": "GROUP_CREATED", "condition_jq": "true"}
        )

        # Reset mock to clear write() calls
        mock_post.reset_mock()

        # Prepare test data
        record_data = test_record.read(["id", "name"])[0]
        test_data = {
            "id": test_record.id,
            "publisher": {"event_type": "GROUP_CREATED"},
            "record_data": record_data,
            "curr_datetime": "2024-12-27T17:05:05.936Z",
        }

        # Test transformation
        self.websub_config.with_context(test_mode=True).publish_by_publisher(test_data)

        # Get the last call arguments
        call_args = mock_post.call_args_list[-1]
        published_data = call_args[1].get("json", {})

        # Verify the transformed data
        self.assertEqual(published_data.get("event"), "GROUP_CREATED")
        self.assertIsNotNone(published_data.get("ts_ms"), "Timestamp should not be None")
        self.assertTrue(isinstance(published_data.get("ts_ms"), str), "Timestamp should be a string")
        # Cleanup
        test_record.unlink()

    @patch("requests.post")
    def test_condition_jq(self, mock_post):
        """Test JQ condition evaluation for event filtering

        Verifies:
            - Events pass through with 'true' condition
            - Events are blocked with 'false' condition
            - Conditional logic works as expected
        """
        mock_post.return_value.ok = True
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "hub.mode=accepted"
        mock_post.return_value.json.return_value = {"access_token": "test_token", "expires_in": 3600}

        # Create test record
        test_record = self.env["res.partner"].create(
            {
                "name": "Test Group",
                "is_group": True,
                "is_registrant": True,
            }
        )

        # Set condition to filter only specific groups - using simple JQ condition
        self.websub_config.write(
            {
                "condition_jq": "true",  # First test with default condition
                "event_type": "GROUP_CREATED",
                "transform_data_jq": ".",
            }
        )

        # Prepare test data
        test_data = {"id": test_record.id, "publisher": {"event_type": "GROUP_CREATED"}}

        # Should pass condition and make API call with default "true" condition
        mock_post.reset_mock()
        self.websub_config.with_context(test_mode=True).publish_by_publisher(test_data)
        self.assertTrue(mock_post.called)

        # Test with false condition
        self.websub_config.write(
            {
                "condition_jq": "false"  # Should prevent publishing
            }
        )

        mock_post.reset_mock()
        self.websub_config.with_context(test_mode=True).publish_by_publisher(test_data)
        self.assertFalse(mock_post.called)

        # Cleanup
        test_record.unlink()

    @patch("requests.post")
    def test_unlink(self, mock_post):
        """Test WebSub configuration deletion

        Verifies:
            - Deregistration API call is made
            - Correct deregistration parameters are sent
        """
        # Setup mock response for deregistration
        mock_post.return_value.ok = True
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "hub.mode=accepted"
        mock_post.return_value.json.return_value = {"access_token": "test_token", "expires_in": 3600}

        # Create a new config for testing unlink
        test_config = self.env["g2p.datashare.config.websub"].create(
            {
                "name": "Test Unlink Config",
                "partner_id": self.env.ref("base.main_partner").id,
                "event_type": "GROUP_CREATED",
                "websub_base_url": "http://test.websub/hub",
                "websub_auth_url": "http://test.auth/token",
                "websub_auth_client_id": "test_client",
                "websub_auth_client_secret": "test_secret",
            }
        )

        # Reset mock to clear creation calls
        mock_post.reset_mock()

        # Unlink the config
        test_config.unlink()

        # Verify deregistration call was made
        self.assertTrue(mock_post.called)
        call_kwargs = mock_post.call_args[1]
        self.assertIn("data", call_kwargs)
        self.assertEqual(call_kwargs["data"]["hub.mode"], "deregister")

    def test_get_image_base64_data_in_url(self):
        """Test image base64 to URL conversion utility

        Verifies:
            - Handles empty/None inputs
            - Correctly formats base64 image data as data URL
            - Maintains image data integrity
        """
        # Test with empty/None image
        result = self.websub_config.get_image_base64_data_in_url("")
        self.assertIsNone(result)

        result = self.websub_config.get_image_base64_data_in_url(None)
        self.assertIsNone(result)

        # This is a tiny 1x1 transparent PNG image
        test_image_base64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        )

        result = self.websub_config.get_image_base64_data_in_url(test_image_base64)

        # Verify the result format
        self.assertTrue(result.startswith("data:image/png;base64,"))
        self.assertIn(test_image_base64, result)
