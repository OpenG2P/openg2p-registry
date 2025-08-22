import graphene

from odoo.addons.g2p_registry_g2p_connect_rest_api.schemas.graphql_schema import (
    GroupMembershipIds,
    PartnerBase,
)
from odoo.addons.g2p_registry_g2p_connect_rest_api.schemas.graphql_schema import Query as BaseQuery


class Partner(PartnerBase):
    group_membership_ids = graphene.Field(graphene.List(GroupMembershipIds))
    is_group = graphene.Boolean(required=True)
    kind = graphene.String()
    is_partial_group = graphene.Boolean()

    # Social Status Information
    num_preg_lact_women = graphene.Int()
    num_malnourished_children = graphene.Int()
    num_disabled = graphene.Int()
    type_of_disability = graphene.String()
    caste_ethnic_group = graphene.String()
    belong_to_protected_groups = graphene.String()
    other_vulnerable_status = graphene.String()

    # Economic Status Information
    income_sources = graphene.String()
    annual_income = graphene.String()
    owns_two_wheeler = graphene.String()
    owns_three_wheeler = graphene.String()
    owns_four_wheeler = graphene.String()
    owns_cart = graphene.String()
    land_ownership = graphene.String()
    type_of_land_owned = graphene.String()
    land_size = graphene.Float()
    owns_house = graphene.String()
    owns_livestock = graphene.String()

    # Households Details
    education_level = graphene.String()
    employment_status = graphene.String()
    marital_status = graphene.String()
    occupation = graphene.String()
    income = graphene.Float()


class Query(BaseQuery):
    get_registrants = graphene.List(
        Partner,
        required=True,
        is_group=graphene.Boolean(),
        limit=graphene.Int(),
        offset=graphene.Int(),
        order=graphene.String(),
        last_sync_date=graphene.DateTime(),
        **{
            key: graphene.String()
            for key in Partner._meta.fields
            if key not in ("reg_ids", "group_membership_ids", "is_group")
        },
    )

    total_registrant_count = graphene.Int()


schema = graphene.Schema(query=Query)
