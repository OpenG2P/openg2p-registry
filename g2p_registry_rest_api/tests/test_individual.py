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
        env = mock_env.return_value

        # distinct mocks per model
        id_type_model = MagicMock()
        reg_id_model = MagicMock()
        id_type_model.sudo.return_value = id_type_model
        reg_id_model.sudo.return_value = reg_id_model

        def getitem_side_effect(key):
            if key == "g2p.id.type":
                return id_type_model
            if key == "g2p.reg.id":
                return reg_id_model
            return MagicMock()

        env.__getitem__.side_effect = getitem_side_effect
        ssn_type = MagicMock()
        ssn_type.id = 1
        ssn_type.name = "SSN"
        dl_type = MagicMock()
        dl_type.id = 2
        dl_type.name = "DL"

        def id_type_search_side_effect(domain, limit=None):
            operator = domain[0][1]
            value = domain[0][2]
            if operator == "in":
                return [id_type for id_type in [ssn_type, dl_type] if id_type.name in value]
            if value == "SSN":
                return ssn_type
            if value == "DL":
                return dl_type
            return False

        id_type_model.search.side_effect = id_type_search_side_effect

        partner = MagicMock(active=True, is_registrant=True, is_group=False)
        partner.reg_ids = MagicMock()
        partner.reg_ids.filtered.return_value = []  # no exclude IDs

        reg = MagicMock(value="123-45-6789", status="valid", partner_id=partner)
        reg_id_model.search.return_value = [reg]

        result = asyncio.run(get_individual_ids(env=env, include_id_type="SSN", exclude_id_type="DL"))
        self.assertEqual(result, ["123-45-6789"])

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_get_individual_ids_multiple_include_types_success(
        self, mock_env, mock_authenticated_partner_env
    ):
        env = mock_env.return_value

        id_type_model = MagicMock()
        reg_id_model = MagicMock()
        id_type_model.sudo.return_value = id_type_model
        reg_id_model.sudo.return_value = reg_id_model

        def getitem_side_effect(key):
            if key == "g2p.id.type":
                return id_type_model
            if key == "g2p.reg.id":
                return reg_id_model
            return MagicMock()

        env.__getitem__.side_effect = getitem_side_effect

        rid_type = MagicMock()
        rid_type.id = 1
        rid_type.name = "RID"
        fan_type = MagicMock()
        fan_type.id = 2
        fan_type.name = "FAN"
        fin_type = MagicMock()
        fin_type.id = 3
        fin_type.name = "FIN"

        def id_type_search_side_effect(domain, limit=None):
            operator = domain[0][1]
            value = domain[0][2]
            if operator == "in":
                return [id_type for id_type in [rid_type, fan_type, fin_type] if id_type.name in value]
            return False

        id_type_model.search.side_effect = id_type_search_side_effect

        partner_1 = MagicMock(id=10, active=True, is_registrant=True, is_group=False)
        partner_1.reg_ids = MagicMock()

        partner_2 = MagicMock(id=20, active=True, is_registrant=True, is_group=False)
        partner_2.reg_ids = MagicMock()

        for partner in [partner_1, partner_2]:
            partner.reg_ids.filtered.return_value = []

        reg_id_model.search.return_value = [
            MagicMock(value="rid1", id_type=rid_type, partner_id=partner_1),
            MagicMock(value="fan1", id_type=fan_type, partner_id=partner_1),
            MagicMock(value="fin1", id_type=fin_type, partner_id=partner_1),
            MagicMock(value="rid2", id_type=rid_type, partner_id=partner_2),
            MagicMock(value="fan2", id_type=fan_type, partner_id=partner_2),
            MagicMock(value="fin2", id_type=fin_type, partner_id=partner_2),
        ]

        result = asyncio.run(get_individual_ids(env=env, include_id_type=["RID", "FAN", "FIN"]))

        self.assertEqual(result, [["rid1", "fan1", "fin1"], ["rid2", "fan2", "fin2"]])

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.api.Environment")
    def test_get_individual_ids_multiple_include_types_with_missing_values(
        self, mock_env, mock_authenticated_partner_env
    ):
        env = mock_env.return_value

        id_type_model = MagicMock()
        reg_id_model = MagicMock()
        id_type_model.sudo.return_value = id_type_model
        reg_id_model.sudo.return_value = reg_id_model

        def getitem_side_effect(key):
            if key == "g2p.id.type":
                return id_type_model
            if key == "g2p.reg.id":
                return reg_id_model
            return MagicMock()

        env.__getitem__.side_effect = getitem_side_effect

        rid_type = MagicMock()
        rid_type.id = 1
        rid_type.name = "RID"
        fan_type = MagicMock()
        fan_type.id = 2
        fan_type.name = "FAN"

        def id_type_search_side_effect(domain, limit=None):
            operator = domain[0][1]
            value = domain[0][2]
            if operator == "in":
                return [id_type for id_type in [rid_type, fan_type] if id_type.name in value]
            return False

        id_type_model.search.side_effect = id_type_search_side_effect

        partner = MagicMock(id=10, active=True, is_registrant=True, is_group=False)
        partner.reg_ids = MagicMock()
        partner.reg_ids.filtered.return_value = []

        reg_id_model.search.return_value = [
            MagicMock(value="rid1", id_type=rid_type, partner_id=partner),
        ]

        result = asyncio.run(get_individual_ids(env=env, include_id_type=["RID", "FAN"]))

        self.assertEqual(result, [["rid1", None]])

    @patch("odoo.addons.fastapi.dependencies.authenticated_partner_env")
    @patch("odoo.addons.g2p_registry_rest_api.routers.individual._logger.exception")
    @patch("odoo.api.Environment")
    def test_get_individual_ids_exception(
        self, mock_env, mock_authenticated_partner_env, mock_logger_exception
    ):
        env = mock_env.return_value

        id_type_model = MagicMock()
        id_type_model.sudo.return_value = id_type_model

        def getitem_side_effect(key):
            if key == "g2p.id.type":
                return id_type_model
            if key == "g2p.reg.id":
                return MagicMock()
            return MagicMock()

        env.__getitem__.side_effect = getitem_side_effect

        id_type_model.search.side_effect = Exception("TEST_EXCEPTION")

        with self.assertRaises(G2PApiValidationError) as context:
            asyncio.run(get_individual_ids(env=env, include_id_type="SSN", exclude_id_type="DL"))

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

        # ID type exists
        mock_id_type = MagicMock()
        mock_id_type.id = 1
        mock_id_type.name = "SSN"
        mock_env.return_value["g2p.id.type"].sudo().search.return_value = mock_id_type

        # But no reg_id matches this value+type
        mock_env.return_value["g2p.reg.id"].sudo().search.return_value = []
        with self.assertRaises(G2PApiValidationError) as context:
            asyncio.run(update_individual(requests=[mock_request], env=mock_env.return_value, id_type="SSN"))

        self.assertIn(
            context.exception.error_message,
            ["Individual with the given ID '999-99-9999' and type 'SSN' not found.", "Unknown ID type: SSN"],
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

        # IMPORTANT: reg_id.partner_id must be the partner we expect to be written
        mock_reg_id.partner_id = mock_individual

        mock_reg_ids = [(0, 0, {"id_type": 1, "value": "123-45-6789", "status": "valid"})]
        mock_processed = {"name": "Updated Individual", "reg_ids": mock_reg_ids}
        mock_env.return_value[
            "process_individual.rest.mixin"
        ]._process_individual.return_value = mock_processed

        # New behavior: update_individual uses g2p.id.type and g2p.reg.id, not res.partner.search
        mock_env.return_value["g2p.id.type"].sudo().search.return_value = mock_id_type
        mock_env.return_value["g2p.reg.id"].sudo().search.return_value = mock_reg_id

        # Old line is no longer used and can be removed:
        # mock_env.return_value["res.partner"].sudo().search.return_value = mock_individual

        with patch("pydantic.BaseModel.model_validate", return_value=mock_individual):
            result = asyncio.run(
                update_individual(
                    requests=[mock_request],
                    env=mock_env.return_value,
                    id_type="SSN",
                )
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

        # This id_type is used only for the existing reg_id on the partner (DL)
        mock_id_type = MagicMock()
        mock_id_type.id = 2
        mock_id_type.name = "DL"

        mock_reg_id = MagicMock()
        mock_reg_id.id = 100
        mock_reg_id.id_type = mock_id_type
        mock_reg_id.value = "DL123456"
        mock_reg_id.status = "valid"

        mock_recordset = MagicMock()
        # filtered() returns False -> no matching reg_ids to update
        mock_recordset.filtered = MagicMock(return_value=False)

        mock_individual = MagicMock()
        mock_individual.id = 1
        mock_individual.name = "Updated Individual"
        mock_individual.reg_ids = mock_recordset

        # processed input (with SSN)
        mock_reg_ids = [(0, 0, {"id_type": 1, "value": "123-45-6789", "status": "valid"})]
        mock_processed = {"name": "Updated Individual", "reg_ids": mock_reg_ids}
        mock_env.return_value[
            "process_individual.rest.mixin"
        ]._process_individual.return_value = mock_processed

        # Router now uses g2p.id.type and g2p.reg.id
        mock_id_type_for_router = MagicMock()
        mock_id_type_for_router.id = 1
        mock_id_type_for_router.name = "SSN"

        mock_env.return_value["g2p.id.type"].sudo().search.return_value = mock_id_type_for_router

        mock_reg_for_router = MagicMock()
        mock_reg_for_router.id = 200
        mock_reg_for_router.partner_id = mock_individual
        mock_env.return_value["g2p.reg.id"].sudo().search.return_value = mock_reg_for_router

        with patch("pydantic.BaseModel.model_validate", return_value=mock_individual):
            result = asyncio.run(
                update_individual(requests=[mock_request], env=mock_env.return_value, id_type="SSN")
            )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, "Updated Individual")

        mock_individual.write.assert_called_once()
        actual_write_args = mock_individual.write.call_args[0][0]
        # reg_ids should remain as originally processed, because filtered() returned False
        self.assertEqual(actual_write_args["reg_ids"][0], mock_reg_ids[0])
