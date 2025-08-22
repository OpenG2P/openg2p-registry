import graphene
from graphene import List

from odoo.addons.graphql_base import OdooObjectType


class RegIds(OdooObjectType):
    id_type_as_str = graphene.String(required=True)
    value = graphene.String(required=True)
    expiry_date = graphene.Date()


class PhoneNumberIds(OdooObjectType):
    phone_no = graphene.String()
    phone_sanitized = graphene.String()
    date_collected = graphene.Date()
    disabled = graphene.Date()


class PartnerBase(OdooObjectType):
    name = graphene.String(required=True)
    given_name = graphene.String()
    family_name = graphene.String()
    addl_name = graphene.String()
    registration_date = graphene.Date()
    address = graphene.String()
    email = graphene.String()
    # district = graphene.String()
    birth_place = graphene.String()
    birthdate = graphene.Date()
    gender = graphene.String()
    reg_ids = graphene.Field(List(RegIds))
    phone_number_ids = graphene.Field(List(PhoneNumberIds))
    create_date = graphene.Date()
    write_date = graphene.Date()


class MemberKind(OdooObjectType):
    name = graphene.String()


class GroupMembershipIds(OdooObjectType):
    individual = graphene.Field(PartnerBase)
    kind = graphene.Field(MemberKind)
    create_date = graphene.Date()
    write_date = graphene.Date()


class Partner(PartnerBase):
    group_membership_ids = graphene.Field(List(GroupMembershipIds))
    is_group = graphene.Boolean(required=True)
    kind = graphene.String()
    is_partial_group = graphene.Boolean()


class Query(graphene.ObjectType):
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

    @staticmethod
    def resolve_get_registrants(
        root, info, last_sync_date=None, is_group: bool = None, limit=None, order=None, offset=None, **kwargs
    ):
        global count

        domain = [(("is_registrant", "=", True))]

        if is_group is not None:
            domain.append(("is_group", "=", is_group))

        if last_sync_date is not None:
            domain.append(("create_date", ">", last_sync_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")))

        for key, value in kwargs.items():
            if value is not None:
                domain.append((key, "=", value))

        partners = (
            info.context["env"]["res.partner"].sudo().search(domain, limit=limit, offset=offset, order=order)
        )

        count = len(partners)
        return partners

    @staticmethod
    def resolve_total_registrant_count(root, info):
        return count


schema = graphene.Schema(query=Query, mutation=None)
