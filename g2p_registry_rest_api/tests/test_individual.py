import asyncio
from unittest.mock import MagicMock, patch

from extendable import context, registry

from odoo.tests import TransactionCase, tagged

from ..exceptions.base_exception import G2PApiValidationError
from ..routers.individual import (
    create_individual,
    get_individual,
    get_individual_ids,
    search_individuals,
    update_individual,
)
from ..schemas.individual import IndividualInfoRequest, UpdateIndividualInfoRequest


@tagged("post_install", "-at_install")
class TestIndividualRouter(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Initialize the Extendable registry
        _registry = registry.ExtendableClassesRegistry()
        context.extendable_registry.set(_registry)
        _registry.init_registry()

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_get_individual_success(self, mock_env, mock_authenticated_partner_env):
        # Test get_individual method for successful response
        individual_id = 1
        mock_individual = MagicMock()
        mock_individual.id = individual_id
        mock_individual.name = "Test Individual"
        mock_individual.is_registrant = True
        mock_individual.is_group = False

        mock_env.return_value["res.partner"].sudo().search.return_value = [mock_individual]

        with patch("pydantic.BaseModel.model_validate", return_value=mock_individual):
            result = asyncio.run(get_individual(individual_id, env=mock_env.return_value))

        self.assertEqual(result.name, "Test Individual")
        self.assertTrue(result.is_registrant)
        self.assertFalse(result.is_group)

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_get_individual_not_found(self, mock_env, mock_authenticated_partner_env):
        # Test get_individual method with invalid individual id
        individual_id = 999
        mock_env.return_value["res.partner"].sudo().search.return_value = []

        with self.assertRaises(G2PApiValidationError) as context:
            asyncio.run(get_individual(individual_id, env=mock_env.return_value))

        self.assertEqual(context.exception.error_message, "Record is not present in the database.")

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_search_individuals_success(self, mock_env, mock_authenticated_partner_env):
        # Test search_individual method for successful response
        mock_individual = MagicMock()
        mock_individual.id = 1
        mock_individual.name = "Test Individual"
        mock_individual.is_registrant = True
        mock_individual.is_group = False

        mock_env.return_value["res.partner"].sudo().search.return_value = [mock_individual]

        with patch("pydantic.BaseModel.model_validate", return_value=mock_individual):
            result = search_individuals(env=mock_env.return_value, name="Test")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Test Individual")

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_search_individuals_not_found(self, mock_env, mock_authenticated_partner_env):
        # Test search_individual method with invalid individual name
        mock_env.return_value["res.partner"].sudo().search.return_value = []

        with self.assertRaises(G2PApiValidationError) as context:
            search_individuals(env=mock_env.return_value, name="Nonexistent")

        self.assertEqual(context.exception.error_message, "The specified criteria did not match any records.")

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_create_individual_success(self, mock_env, mock_authenticated_partner_env):
        # Test create_individual method for successful response
        mock_request = MagicMock(spec=IndividualInfoRequest)
        mock_request.name = "New Individual"
        mock_request.given_name = "John"
        mock_request.gender = "Male"

        mock_individual = MagicMock()
        mock_individual.id = 1
        mock_individual.name = "New Individual"
        mock_individual.given_name = "John"
        mock_individual.gender = "Male"
        mock_individual.is_registrant = True
        mock_individual.is_group = False

        mock_env.return_value["res.partner"].sudo().create.return_value = mock_individual
        mock_env.return_value["res.partner"].sudo().search.return_value = [mock_individual]

        with patch("pydantic.BaseModel.model_validate", return_value=mock_individual):
            result = create_individual(mock_request, env=mock_env.return_value)

        self.assertEqual(result.name, "New Individual")
        self.assertEqual(result.given_name, "John")
        self.assertEqual(result.gender, "Male")

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_get_individual_ids_success(self, mock_env, mock_authenticated_partner_env):
        # Test get_individual_ids method for successful response

        ssn_id_type = MagicMock()
        ssn_id_type.name = "SSN"

        mock_ssn_reg_id = MagicMock()
        mock_ssn_reg_id.id_type = ssn_id_type
        mock_ssn_reg_id.value = "123-45-6789"
        mock_ssn_reg_id.status = "valid"

        mock_individual = MagicMock()
        mock_individual.reg_ids = [mock_ssn_reg_id]

        mock_env.return_value["res.partner"].sudo().search.return_value = [mock_individual]

        result = asyncio.run(
            get_individual_ids(env=mock_env.return_value, include_id_type="SSN", exclude_id_type="DL")
        )

        self.assertEqual(result, ["123-45-6789"])

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_get_individual_ids_exception(self, mock_env, mock_authenticated_partner_env):
        # Test get_individual_ids method with exception while fetching partner

        ssn_id_type = MagicMock()
        ssn_id_type.name = "SSN"

        mock_ssn_reg_id = MagicMock()
        mock_ssn_reg_id.id_type = ssn_id_type
        mock_ssn_reg_id.value = "123-45-6789"
        mock_ssn_reg_id.status = "valid"

        mock_individual = MagicMock()
        mock_individual.reg_ids = [mock_ssn_reg_id]

        mock_env.return_value["res.partner"].sudo().search.side_effect = Exception("TEST_EXCEPTION")

        with self.assertRaises(G2PApiValidationError) as context:
            asyncio.run(
                get_individual_ids(env=mock_env.return_value, include_id_type="SSN", exclude_id_type="DL")
            )

        self.assertEqual(context.exception.error_message, "An error occurred while getting IDs.")

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_get_individual_ids_missing_include_type(self, mock_env, mock_authenticated_partner_env):
        # Test get_individual_ids method with missing individual
        with self.assertRaises(G2PApiValidationError) as context:
            asyncio.run(get_individual_ids(env=mock_env.return_value))

        self.assertEqual(context.exception.error_message, "Record is not present in the database.")

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_update_individual_success(self, mock_env, mock_authenticated_partner_env):
        # Test update_individual method for successful response
        mock_request = MagicMock(spec=UpdateIndividualInfoRequest)
        mock_request.updateId = "123-45-6789"
        mock_request.name = "Updated Individual"
        mock_request.given_name = "John"
        mock_request.gender = "Male"

        mock_individual = MagicMock()
        mock_individual.id = 1
        mock_individual.name = "Updated Individual"
        mock_individual.reg_ids = [
            MagicMock(id_type=MagicMock(id=1, name="SSN"), value="123-45-6789", status="valid")
        ]

        mock_env.return_value["res.partner"].sudo().search.return_value = mock_individual

        with patch("pydantic.BaseModel.model_validate", return_value=mock_individual):
            result = asyncio.run(
                update_individual(requests=[mock_request], env=mock_env.return_value, id_type="SSN")
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Updated Individual")

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_update_individual_not_found(self, mock_env, mock_authenticated_partner_env):
        # Test update_individual method passing invalid id
        mock_request = MagicMock(spec=UpdateIndividualInfoRequest)
        mock_request.updateId = "999-99-9999"

        mock_env.return_value["res.partner"].sudo().search.return_value = None

        with self.assertRaises(G2PApiValidationError) as context:
            asyncio.run(update_individual(requests=[mock_request], env=mock_env.return_value, id_type="SSN"))

        self.assertEqual(
            context.exception.error_message, "Individual with the given ID 999-99-9999 not found."
        )

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_update_individual_missing_id(self, mock_env, mock_authenticated_partner_env):
        # Test update_individual method without passing new id
        mock_request = MagicMock(spec=UpdateIndividualInfoRequest)
        mock_request.updateId = None

        with self.assertRaises(G2PApiValidationError) as context:
            asyncio.run(update_individual(requests=[mock_request], env=mock_env.return_value, id_type="SSN"))

        self.assertEqual(context.exception.error_message, "ID is required for update individual")

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_update_individual_with_matching_reg_ids(self, mock_env, mock_authenticated_partner_env):
        # Test update_individual when there are matching registration ids to update
        mock_request = MagicMock(spec=UpdateIndividualInfoRequest)
        mock_request.updateId = "123-45-6789"
        mock_request.name = "Updated Individual"

        mock_id_type = MagicMock()
        mock_id_type.id = 1
        mock_id_type.name = "SSN"

        mock_reg_id = MagicMock()
        mock_reg_id.id = 100
        mock_reg_id.id_type = mock_id_type
        mock_reg_id.value = "123-45-6789"
        mock_reg_id.status = "valid"

        mock_recordset = MagicMock()
        mock_recordset.filtered = MagicMock(return_value=mock_reg_id)

        mock_individual = MagicMock()
        mock_individual.id = 1
        mock_individual.name = "Updated Individual"
        mock_individual.reg_ids = mock_recordset

        mock_reg_ids = [(0, 0, {"id_type": 1, "value": "123-45-6789", "status": "valid"})]
        mock_processed = {"name": "Updated Individual", "reg_ids": mock_reg_ids}
        mock_env.return_value[
            "process_individual.rest.mixin"
        ]._process_individual.return_value = mock_processed

        mock_env.return_value["res.partner"].sudo().search.return_value = mock_individual

        with patch("pydantic.BaseModel.model_validate", return_value=mock_individual):
            result = asyncio.run(
                update_individual(requests=[mock_request], env=mock_env.return_value, id_type="SSN")
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Updated Individual")

        expected_reg_ids = [(1, 100, {"id_type": 1, "value": "123-45-6789", "status": "valid"})]
        mock_individual.write.assert_called_once()
        actual_write_args = mock_individual.write.call_args[0][0]
        self.assertEqual(actual_write_args["reg_ids"][0][0], expected_reg_ids[0][0])
        self.assertEqual(actual_write_args["reg_ids"][0][1], expected_reg_ids[0][1])
        self.assertEqual(actual_write_args["reg_ids"][0][2], expected_reg_ids[0][2])

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_update_individual_with_non_matching_reg_ids(self, mock_env, mock_authenticated_partner_env):
        # Test update_individual when there are no matching registration ids
        mock_request = MagicMock(spec=UpdateIndividualInfoRequest)
        mock_request.updateId = "123-45-6789"
        mock_request.name = "Updated Individual"

        mock_id_type = MagicMock()
        mock_id_type.id = 2
        mock_id_type.name = "DL"

        mock_reg_id = MagicMock()
        mock_reg_id.id = 100
        mock_reg_id.id_type = mock_id_type
        mock_reg_id.value = "DL123456"
        mock_reg_id.status = "valid"

        mock_recordset = MagicMock()
        mock_recordset.filtered = MagicMock(return_value=False)

        mock_individual = MagicMock()
        mock_individual.id = 1
        mock_individual.name = "Updated Individual"
        mock_individual.reg_ids = mock_recordset

        mock_reg_ids = [(0, 0, {"id_type": 1, "value": "123-45-6789", "status": "valid"})]
        mock_processed = {"name": "Updated Individual", "reg_ids": mock_reg_ids}
        mock_env.return_value[
            "process_individual.rest.mixin"
        ]._process_individual.return_value = mock_processed

        mock_env.return_value["res.partner"].sudo().search.return_value = mock_individual

        with patch("pydantic.BaseModel.model_validate", return_value=mock_individual):
            result = asyncio.run(
                update_individual(requests=[mock_request], env=mock_env.return_value, id_type="SSN")
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Updated Individual")

        mock_individual.write.assert_called_once()
        actual_write_args = mock_individual.write.call_args[0][0]
        self.assertEqual(actual_write_args["reg_ids"][0], mock_reg_ids[0])
