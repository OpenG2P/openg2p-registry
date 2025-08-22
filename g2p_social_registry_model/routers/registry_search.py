from odoo.addons.g2p_registry_g2p_connect_rest_api.routers import registry_search

from ..schemas import graphql_schema


def get_graphql_schema():
    return graphql_schema.schema.graphql_schema


registry_search.get_graphql_schema = get_graphql_schema
