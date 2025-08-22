from odoo.addons.g2p_registry_rest_api.schemas.group import GroupInfoRequest, GroupInfoResponse


class SocialRegistryDemoGroupInfoResponse(GroupInfoResponse, extends=GroupInfoResponse):
    # Social Status Information
    num_preg_lact_women: int | None = None
    num_malnourished_children: int | None = None
    num_disabled: int | None = None
    type_of_disability: str | None = None
    caste_ethnic_group: str | None = None
    belong_to_protected_groups: str | None = None
    other_vulnerable_status: str | None = None

    # Economic Status Information
    income_sources: str | None = None
    annual_income: str | None = None
    owns_two_wheeler: str | None = None
    owns_three_wheeler: str | None = None
    owns_four_wheeler: str | None = None
    owns_cart: str | None = None
    land_ownership: str | None = None
    type_of_land_owned: str | None = None
    land_size: float | None = None
    owns_house: str | None = None
    owns_livestock: str | None = None


class SocialRegistryDemoGroupInfoRequest(GroupInfoRequest, extends=GroupInfoRequest):
    # Social Status Information
    num_preg_lact_women: int | None = None
    num_malnourished_children: int | None = None
    num_disabled: int | None = None
    type_of_disability: str | None = None
    caste_ethnic_group: str | None = None
    belong_to_protected_groups: str | None = None
    other_vulnerable_status: str | None = None

    # Economic Status Information
    income_sources: str | None = None
    annual_income: str | None = None
    owns_two_wheeler: str | None = None
    owns_three_wheeler: str | None = None
    owns_four_wheeler: str | None = None
    owns_cart: str | None = None
    land_ownership: str | None = None
    type_of_land_owned: str | None = None
    land_size: float | None = None
    owns_house: str | None = None
    owns_livestock: str | None = None
