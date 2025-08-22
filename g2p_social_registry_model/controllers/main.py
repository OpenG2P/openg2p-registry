import logging

from odoo import http
from odoo.http import request

from odoo.addons.g2p_registration_portal_base.controllers.main import G2PregistrationPortalBase

_logger = logging.getLogger(__name__)


class G2PSocialRegistryModel(G2PregistrationPortalBase):
    @http.route(
        ["/portal/registration/group/create/submit"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def group_create_submit(self, **kw):
        try:
            head_name = kw.get("name")
            beneficiary_id = None

            additional_data = {
                "name": head_name,
                "birthdate": kw.get("birthdate"),
                "gender": kw.get("gender"),
                "email": kw.get("email"),
                "address": kw.get("address"),
                # Social Status Information
                "num_preg_lact_women": int(kw.get("num_preg_lact_women", 0))
                if kw.get("num_preg_lact_women")
                else 0,
                "num_malnourished_children": int(kw.get("num_malnourished_children", 0))
                if kw.get("num_malnourished_children")
                else 0,
                "num_disabled": int(kw.get("num_disabled", 0)) if kw.get("num_disabled") else 0,
                "type_of_disability": kw.get("type_of_disability"),
                # Economic Status Information
                "caste_ethnic_group": kw.get("caste_ethnic_group"),
                "belong_to_protected_groups": kw.get("belong_to_protected_groups"),
                "other_vulnerable_status": kw.get("other_vulnerable_status"),
                "income_sources": kw.get("income_sources"),
                "annual_income": kw.get("annual_income", False),
                "owns_two_wheeler": kw.get("owns_two_wheeler"),
                "owns_three_wheeler": kw.get("owns_three_wheeler"),
                "owns_four_wheeler": kw.get("owns_four_wheeler"),
                "owns_cart": kw.get("owns_cart"),
                "land_ownership": kw.get("land_ownership"),
                "type_of_land_owned": kw.get("type_of_land_owned"),
                "land_size": float(kw.get("land_size", 0.0)) if kw.get("land_size") else 0.0,
                "owns_house": kw.get("owns_house"),
                "owns_livestock": kw.get("owns_livestock"),
            }

            if kw.get("group_id"):
                beneficiary = request.env["res.partner"].sudo().browse(int(kw.get("group_id")))
                beneficiary.write(additional_data)
                beneficiary_id = beneficiary.id
            else:
                if head_name:
                    user = request.env.user

                    data = {
                        "is_registrant": True,
                        "is_group": True,
                        "user_id": user.id,
                    }

                    data.update(additional_data)
                    beneficiary_obj = request.env["res.partner"].sudo().create(data)
                    beneficiary_id = beneficiary_obj.id

                    # Create a group head as member
                    head_name_parts = head_name.split(" ")
                    h_given_name = head_name_parts[0]
                    h_family_name = head_name_parts[-1]

                    if len(head_name_parts) > 2:
                        h_addl_name = " ".join(head_name_parts[1:-1])
                    else:
                        h_addl_name = ""

                    formatted_name = f"{h_family_name} , {h_given_name} {h_addl_name}"

                    head_individual = (
                        request.env["res.partner"]
                        .sudo()
                        .create(
                            {
                                "name": formatted_name,
                                "given_name": h_given_name,
                                "addl_name": h_addl_name,
                                "family_name": h_family_name,
                                "email": kw.get("email"),
                                "address": kw.get("address"),
                                "birthdate": kw.get("birthdate"),
                                "gender": kw.get("gender"),
                                "is_registrant": True,
                                "is_group": False,
                                "user_id": user.id,
                            }
                        )
                    )

                    # Create membership relationship between head and group
                    group_membership_vals = [
                        (0, 0, {"individual": head_individual.id, "group": beneficiary_id})
                    ]

                    # Update the group with this membership
                    beneficiary_obj.write({"group_membership_ids": group_membership_vals})

            beneficiary = request.env["res.partner"].sudo().browse(beneficiary_id)

            if not beneficiary:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": "Beneficiary not found."},
                )

            return request.redirect("/portal/registration/group")

        except Exception as e:
            _logger.error("Error occurred: %s" % e)
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "An error occurred. Please try again later."},
            )

    @http.route(
        ["/portal/registration/individual/create/submit"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def individual_create_submit(self, **kw):
        try:
            user = request.env.user
            name = ""
            if kw.get("family_name"):
                name += kw.get("family_name") + ", "
            if kw.get("given_name"):
                name += kw.get("given_name") + " "
            if kw.get("addl_name"):
                name += kw.get("addl_name") + " "
            if kw.get("birthdate") == "":
                birthdate = False
            else:
                birthdate = kw.get("birthdate")

            data = {
                "given_name": kw.get("given_name"),
                "addl_name": kw.get("addl_name"),
                "family_name": kw.get("family_name"),
                "name": name.strip(),
                "birthdate": birthdate,
                "gender": kw.get("gender"),
                "email": kw.get("email"),
                "user_id": user.id,
                "is_registrant": True,
                "is_group": False,
                # Additional fields
                "address": kw.get("address"),
                "occupation": kw.get("occupation"),
                "income": float(kw.get("income", 0.0)) if kw.get("income") else 0.0,
                "education_level": kw.get("education_level"),
                "employment_status": kw.get("employment_status"),
                "marital_status": kw.get("marital_status"),
            }

            request.env["res.partner"].sudo().create(data)

            return request.redirect("/portal/registration/individual")

        except Exception as e:
            _logger.exception("Error while submitting individual registration: %s", str(e))
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "Error while submitting individual registration"},
            )

    @http.route(
        "/portal/registration/individual/update/submit",
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def update_individual_submit(self, **kw):
        try:
            member = request.env["res.partner"].sudo().browse(int(kw.get("group_id")))
            if member:
                name = ""
                if kw.get("family_name"):
                    name += kw.get("family_name") + ", "
                if kw.get("given_name"):
                    name += kw.get("given_name") + " "
                if kw.get("addl_name"):
                    name += kw.get("addl_name") + " "
                if kw.get("birthdate") == "":
                    birthdate = False
                else:
                    birthdate = kw.get("birthdate")

                member.sudo().write(
                    {
                        "given_name": kw.get("given_name"),
                        "addl_name": kw.get("addl_name"),
                        "family_name": kw.get("family_name"),
                        "name": name,
                        "birthdate": birthdate,
                        "gender": kw.get("gender"),
                        "email": kw.get("email"),
                        "address": kw.get("address"),
                        "occupation": kw.get("occupation"),
                        "income": float(kw.get("income", 0.0)),
                        # Household Details
                        "education_level": kw.get("education_level"),
                        "employment_status": kw.get("employment_status"),
                        "marital_status": kw.get("marital_status"),
                    }
                )
            return request.redirect("/portal/registration/individual")

        except Exception as e:
            _logger.error("Error occurred%s" % e)
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "An error occurred. Please try again later."},
            )
