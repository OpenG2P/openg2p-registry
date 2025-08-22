import json
from datetime import datetime, timezone
from unittest.mock import patch

import requests

from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("-at_install", "post_install")
class TestRegistrySearchAPITestCase(HttpCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Partner", "is_registrant": True})
        self.payload = {
            "signature": "string",
            "header": {
                "version": "1.0.0",
                "message_id": "",
                "message_ts": f"{datetime.now(timezone.utc).isoformat()}",
                "action": "search",
                "sender_id": "",
                "sender_uri": "",
                "receiver_id": "",
                "total_count": 0,
                "is_msg_encrypted": False,
                "meta": {},
            },
            "message": {
                "transaction_id": "",
                "search_request": [
                    {
                        "reference_id": "",
                        "timestamp": f"{datetime.now(timezone.utc).isoformat()}",
                        "search_criteria": {
                            "version": "1.0.0",
                            "reg_type": "",
                            "reg_sub_type": "",
                            "query_type": "graphql",
                            "query": '{getRegistrants(name: "Test Partner"){name}}',
                        },
                        "locale": "en",
                    }
                ],
            },
        }

    def test_registry_serach_api_empty_authorization_header(self):
        res = self.url_open(
            "/api/v1/g2p-connect/registry/sync/search",
            data=json.dumps(self.payload),
            headers={"content-type": "application/json"},
        )

        self.assertEqual(401, res.status_code)
        self.assertTrue("Missing authorization header.", res.json()["detail"])

    @patch("odoo.addons.g2p_registry_g2p_connect_rest_api.routers.registry_search.requests.get")
    @patch("odoo.addons.g2p_registry_g2p_connect_rest_api.routers.registry_search.jwt.decode")
    def test_registry_search_api_invalid_token(self, mock_jwt_decode, mock_requests_get):
        mock_requests_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "Invalid JWKS"
        )
        mock_jwt_decode.return_value = False, "Invalid token"

        res = self.url_open(
            "/api/v1/g2p-connect/registry/sync/search",
            data=json.dumps(self.payload),
            headers={"Authorization": "Bearer invalid_token", "content-type": "application/json"},
        )

        self.assertEqual(401, res.status_code)
        self.assertTrue("Invalid Access Token", res.json()["detail"])

    @patch("odoo.addons.g2p_registry_g2p_connect_rest_api.routers.registry_search.requests.get")
    @patch("odoo.addons.g2p_registry_g2p_connect_rest_api.routers.registry_search.jwt.decode")
    def test_registry_search_api_jwt_decode_exception(self, mock_jwt_decode, mock_requests_get):
        mock_jwt_decode.side_effect = Exception("JWT decode error")

        res = self.url_open(
            "/api/v1/g2p-connect/registry/sync/search",
            data=json.dumps(self.payload),
            headers={"Authorization": "Bearer valid_token", "content-type": "application/json"},
        )

        self.assertEqual(401, res.status_code)
        self.assertTrue("JWT decode error", res.json()["detail"])

    @patch("odoo.addons.g2p_registry_g2p_connect_rest_api.routers.registry_search.requests.get")
    @patch("odoo.addons.g2p_registry_g2p_connect_rest_api.routers.registry_search.jwt.decode")
    def test_registry_search_api_valid_token(self, mock_requests_get, mock_jwt_decode):
        res = self.url_open(
            "/api/v1/g2p-connect/registry/sync/search",
            data=json.dumps(self.payload),
            headers={"Authorization": "Bearer valid_token", "content-type": "application/json"},
        )

        self.assertEqual(
            "Test Partner",
            res.json()["message"]["search_response"][0]["data"]["reg_records"]["getRegistrants"][0]["name"],
        )

        # Empty query expression
        self.payload["message"]["search_request"][0]["search_criteria"]["query"] = ""

        res = self.url_open(
            "/api/v1/g2p-connect/registry/sync/search",
            data=json.dumps(self.payload),
            headers={"Authorization": "Bearer token", "content-type": "application/json"},
        )

        self.assertEqual("Must provide query string.", res.json()["detail"])

        # Other than Graphql type
        self.payload["message"]["search_request"][0]["search_criteria"]["query_type"] = "Other than graphql"

        res = self.url_open(
            "/api/v1/g2p-connect/registry/sync/search",
            data=json.dumps(self.payload),
            headers={"Authorization": "Bearer token", "content-type": "application/json"},
        )

        self.assertTrue("Only graphql query type supported.", res.json()["detail"])
