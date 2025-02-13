from unittest.mock import MagicMock, patch

from extendable import context, registry

from odoo.tests import TransactionCase, tagged

from ..exceptions.base_exception import G2PApiValidationError
from ..exceptions.error_codes import G2PErrorCodes
from ..routers.group import create_group, get_group, search_groups
from ..schemas.group import GroupInfoRequest
from ..schemas.group_membership import GroupMembershipKindInfo, GroupMembersInfoRequest


@tagged("post_install", "-at_install")
class TestGroupRouter(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Initialize the Extendable registry
        _registry = registry.ExtendableClassesRegistry()
        context.extendable_registry.set(_registry)
        _registry.init_registry()

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_get_group_success(self, mock_env, mock_authenticated_partner_env):
        # Test get_group method for successful response
        group_id = 1
        mock_group = MagicMock()
        mock_group.id = group_id
        mock_group.name = "Test Group"
        mock_group.is_registrant = True
        mock_group.is_group = True

        mock_env.return_value["res.partner"].sudo().search.return_value = [mock_group]

        with patch("pydantic.BaseModel.model_validate", return_value=mock_group):
            result = get_group(group_id, env=mock_env.return_value)

        self.assertEqual(result.name, "Test Group")
        self.assertTrue(result.is_registrant)
        self.assertTrue(result.is_group)

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_get_group_not_found(self, mock_env, mock_authenticated_partner_env):
        # Test get_group method with invalid id
        group_id = 999
        mock_env.return_value["res.partner"].sudo().search.return_value = []

        with self.assertRaises(G2PApiValidationError) as context:
            get_group(group_id, env=mock_env.return_value)

        self.assertEqual(context.exception.error_message, G2PErrorCodes.G2P_REQ_010.get_error_message())
        self.assertEqual(context.exception.error_description, "Record is not present in the database.")

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_search_groups_success(self, mock_env, mock_authenticated_partner_env):
        # Test search_group method for successful response
        group_name = "Test Group"
        mock_group = MagicMock()
        mock_group.id = 1
        mock_group.name = group_name
        mock_group.is_registrant = True
        mock_group.is_group = True

        mock_env.return_value["res.partner"].sudo().search.return_value = [mock_group]

        with patch("pydantic.BaseModel.model_validate", return_value=mock_group):
            result = search_groups(env=mock_env.return_value, name=group_name)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, group_name)

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_search_groups_name_not_found(self, mock_env, mock_authenticated_partner_env):
        # Test search_group method with invalid name
        group_name = "Nonexistent Group"
        mock_env.return_value["res.partner"].sudo().search.return_value = []

        with self.assertRaises(G2PApiValidationError) as context:
            search_groups(env=mock_env.return_value, name=group_name)

        self.assertEqual(context.exception.error_message, G2PErrorCodes.G2P_REQ_010.get_error_message())
        self.assertEqual(
            context.exception.error_description, "This Name does not exist. Please enter a valid Name."
        )

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_search_groups_id_not_found(self, mock_env, mock_authenticated_partner_env):
        # Test search_group method with invalid id
        group_id = 999
        mock_env.return_value["res.partner"].sudo().search.return_value = []

        with self.assertRaises(G2PApiValidationError) as context:
            search_groups(env=mock_env.return_value, _id=group_id)

        self.assertEqual(context.exception.error_message, G2PErrorCodes.G2P_REQ_010.get_error_message())
        self.assertEqual(
            context.exception.error_description, "This ID does not exist. Please enter a valid ID."
        )

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_create_group_success(self, mock_env, mock_authenticated_partner_env):
        # Test create_group method for successful response

        # Using mock spec cause of pydantic validation
        mock_request_data = MagicMock(spec=GroupInfoRequest)
        mock_request_data.is_group = True
        mock_request_data.kind = "Primary Group"
        mock_request_data.is_partial_group = False

        mock_member = MagicMock(spec=GroupMembersInfoRequest)
        mock_member.name = "Test Member"
        mock_member.given_name = "Jane"
        mock_member.gender = "Female"
        mock_member_kind = MagicMock(spec=GroupMembershipKindInfo)
        mock_member_kind.name = "Admin"

        mock_member.kind = [mock_member_kind]
        mock_request_data.members = [mock_member]

        mock_partner = MagicMock()
        mock_partner.id = 1
        mock_partner.name = "New Test Group"
        mock_partner.members = [
            {
                "name": "Member 1",
                "given_name": "John",
                "gender": "Male",
                "kind": [{"name": "Admin"}],
            }
        ]

        mock_kind_id = MagicMock(id=7)

        mock_env.return_value["res.partner"].sudo().create.return_value = mock_partner
        mock_env.return_value["g2p.group.membership.kind"].sudo().search.return_value = [mock_kind_id]

        with patch("pydantic.BaseModel.model_validate", return_value=mock_partner):
            result = create_group(mock_request_data, env=mock_env.return_value)

        assert result.name == "New Test Group"
        assert len(result.members) == 1
        assert result.members[0]["name"] == "Member 1"
        assert result.members[0]["given_name"] == "John"
        assert result.members[0]["gender"] == "Male"
        assert result.members[0]["kind"][0]["name"] == "Admin"

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_create_group_invalid_kind(self, mock_env, mock_authenticated_partner_env):
        # Test create_group method with invalid kind
        mock_request_data = MagicMock(spec=GroupInfoRequest)
        mock_request_data.is_group = True
        mock_request_data.kind = "Primary Group"
        mock_request_data.is_partial_group = False

        mock_member = MagicMock(spec=GroupMembersInfoRequest)
        mock_member.name = "Test Member"
        mock_member.given_name = "Jane"
        mock_member.gender = "Female"

        mock_member_kind = MagicMock(spec=GroupMembershipKindInfo)
        mock_member_kind.name = "Admin"

        mock_member.kind = [mock_member_kind]
        mock_request_data.members = [mock_member]

        # Mock the partner/group creation
        mock_partner = MagicMock()
        mock_partner.id = 1
        mock_partner.name = "New Test Group"
        mock_partner.members = [
            {
                "name": "Member 1",
                "given_name": "John",
                "gender": "Male",
                "kind": [{"name": "Admin"}],
            }
        ]

        # Mock the environment methods
        mock_env.return_value["res.partner"].sudo().create.return_value = mock_partner
        mock_env.return_value["g2p.group.membership.kind"].sudo().search.return_value = []

        with self.assertRaises(G2PApiValidationError) as context:
            create_group(mock_request_data, env=mock_env.return_value)

        self.assertEqual(context.exception.error_message, G2PErrorCodes.G2P_REQ_004.get_error_message())
        self.assertEqual(
            context.exception.error_description, "Membership kind - Admin is not present in the database."
        )
