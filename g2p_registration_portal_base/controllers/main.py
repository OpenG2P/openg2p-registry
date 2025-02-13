import json
import logging

from odoo import http
from odoo.http import request

from odoo.addons.g2p_agent_portal_base.controllers.main import AgentPortalBase

_logger = logging.getLogger(__name__)


class G2PregistrationPortalBase(AgentPortalBase):
    @http.route("/portal/registration/group", type="http", auth="user", website=True)
    def group_list(self, **kw):
        user = request.env.user

        domain = [
            ("active", "=", True),
            ("is_registrant", "=", True),
            ("is_group", "=", True),
        ]

        partner = user.partner_id

        subdomain = [("user_id", "=", user.id)]

        if partner and partner.odk_app_user:
            subdomain = [
                "|",
                ("enumerator_id.enumerator_user_id", "=", partner.odk_app_user.odk_user_id),
                ("user_id", "=", user.id),
            ]

        domain += subdomain

        group = request.env["res.partner"].sudo().search(domain)

        return request.render("g2p_registration_portal_base.group_list", {"groups": group})

    @http.route(
        ["/portal/registration/group/create/"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def group_create(self, **kw):
        gender = request.env["gender.type"].sudo().search([])

        return request.render(
            "g2p_registration_portal_base.group_create_form_template",
            {"gender": gender},
        )

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
            # Group creation
            if kw.get("group_id"):
                beneficiary_id = request.env["res.partner"].sudo().browse(int(kw.get("group_id")))
            else:
                if head_name:
                    user = request.env.user

                    data = {
                        "name": head_name,
                        "is_registrant": True,
                        "is_group": True,
                        "birthdate": kw.get("dob"),
                        "gender": kw.get("gender"),
                        "user_id": user.id,
                    }

                    beneficiary_obj = request.env["res.partner"].sudo().create(data)

                    beneficiary_id = beneficiary_obj.id
            beneficiary = request.env["res.partner"].sudo().browse(beneficiary_id)

            if not beneficiary:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": "Beneficiary not found."},
                )

            for key, value in kw.items():
                if key in beneficiary:
                    beneficiary.write({key: value})
                else:
                    _logger.error(f"Ignoring invalid key: {key}")

            return request.redirect("/portal/registration/group")

        except Exception as e:
            _logger.error("Error occurred%s" % e)
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "An error occurred. Please try again later."},
            )

    @http.route(
        ["/portal/registration/group/update/<int:_id>"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def group_update(self, _id, **kw):
        try:
            gender = request.env["gender.type"].sudo().search([])
            beneficiary = request.env["res.partner"].sudo().browse(_id)

            if not beneficiary:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": "Beneficiary not found."},
                )

            return request.render(
                "g2p_registration_portal_base.group_update_form_template",
                {
                    "beneficiary": beneficiary,
                    "gender": gender,
                    "individuals": beneficiary.group_membership_ids.mapped("individual"),
                },
            )

        except Exception:
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "Invalid URL."},
            )

    @http.route(
        ["/portal/registration/group/update/submit/"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def group_submit(self, **kw):
        try:
            beneficiary_id = int(kw.get("group_id"))

            beneficiary = request.env["res.partner"].sudo().browse(beneficiary_id)
            if not beneficiary:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": "Beneficiary not found."},
                )
            # TODO: Relationship logic need to build later
            if kw.get("relationship"):
                kw.pop("relationship")

            for key, value in kw.items():
                if key in beneficiary:
                    beneficiary.write({key: value})
                else:
                    _logger.error(f"Ignoring invalid key: {key}")

            return request.redirect("/portal/registration/group")

        except Exception as e:
            _logger.error("Error occurred%s" % e)
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "An error occurred. Please try again later."},
            )

    # Creating Group members
    @http.route(
        ["/portal/registration/member/create/"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def individual_create(self, **kw):
        res = dict()
        try:
            head_name = kw.get("household_name")
            head_individual = None
            # Group creation
            if kw.get("group_id"):
                group_rec = request.env["res.partner"].sudo().browse(int(kw.get("group_id")))
            else:
                if head_name:
                    group_rec = (
                        request.env["res.partner"]
                        .sudo()
                        .create({"name": head_name, "is_registrant": True, "is_group": True})
                    )
                    # Head creation
                    head_name_parts = head_name.split(" ")
                    h_given_name = head_name_parts[0]
                    h_family_name = head_name_parts[-1]

                    if len(head_name_parts) > 2:
                        h_addl_name = " ".join(head_name_parts[1:-1])
                    else:
                        h_addl_name = ""

                    name = f"{h_given_name}, {h_addl_name} {h_family_name}"

                    head_individual = (
                        request.env["res.partner"]
                        .sudo()
                        .create(
                            {
                                "given_name": h_given_name,
                                "name": name,
                                "addl_name": h_addl_name,
                                "family_name": h_family_name,
                                "birthdate": kw.get("Household_dob"),
                                "gender": kw.get("Househol_gender"),
                            }
                        )
                    )

            given_name = kw.get("given_name")
            family_name = kw.get("family_name")
            addl_name = kw.get("addl_name")
            user = request.env.user

            name = f"{given_name}, {addl_name} {family_name}"

            partner_data = {
                "name": name,
                "given_name": given_name,
                "family_name": family_name,
                "addl_name": addl_name,
                "birthdate": kw.get("birthdate"),
                "gender": kw.get("gender"),
                "is_registrant": True,
                "is_group": False,
                "user_id": user.id,
            }

            # TODO: Relationship logic need to build later
            if kw.get("relationship"):
                kw.pop("relationship")

            individual = request.env["res.partner"].sudo().create(partner_data)

            # Member creation only if head_individual is created
            group_membership_vals = [(0, 0, {"individual": individual.id, "group": group_rec.id})]

            # Add head_individual membership if created
            if head_individual:
                group_membership_vals.insert(
                    0, (0, 0, {"individual": head_individual.id, "group": group_rec.id})
                )

            group_rec.write({"group_membership_ids": group_membership_vals})

            member_list = []
            for membership in group_rec.group_membership_ids:
                member_list.append(
                    {
                        "id": membership.individual.id,
                        "name": membership.individual.name,
                        "age": membership.individual.age,
                        "gender": membership.individual.gender,
                        "active": membership.individual.active,
                        "group_id": membership.group.id,
                    }
                )

            res["member_list"] = member_list
            return json.dumps(res)

        except Exception as e:
            _logger.error("ERROR LOG IN INDIVIDUAL%s", e)

    @http.route(
        "/portal/registration/member/update/",
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def update_member(self, **kw):
        member_id = kw.get("member_id")
        try:
            beneficiary = request.env["res.partner"].sudo().browse(int(member_id))
            if beneficiary:
                exist_value = {
                    "given_name": beneficiary.given_name,
                    "addl_name": beneficiary.addl_name,
                    "family_name": beneficiary.family_name,
                    "dob": str(beneficiary.birthdate),
                    "gender": beneficiary.gender,
                    "id": beneficiary.id,
                }
                return json.dumps(exist_value)

        except Exception as e:
            _logger.error("ERROR LOG IN UPDATE MEMBER%s", e)

    @http.route(
        "/portal/registration/member/update/submit/",
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def update_member_submit(self, **kw):
        try:
            member = request.env["res.partner"].sudo().browse(int(kw.get("member_id")))
            res = dict()
            if member:
                # birthdate = datetime.strptime(kw["birthdate"], "%Y-%m-%d").date()
                given_name = kw.get("given_name")
                family_name = kw.get("family_name")
                addl_name = kw.get("addl_name")

                name = f"{given_name}, {addl_name} {family_name}"

                member.sudo().write(
                    {
                        "given_name": given_name,
                        "addl_name": addl_name,
                        "name": name,
                        "family_name": family_name,
                        "birthdate": kw.get("birthdate"),
                        "gender": kw.get("gender"),
                    }
                )
                # group = request.env["res.partner"].sudo().browse(int(kw.get("group_id")))
                member_list = []

                for membership in member:
                    member_list.append(
                        {
                            "id": membership.id,
                            "name": membership.name,
                            "age": membership.age,
                            "gender": membership.gender,
                            "active": membership.active,
                        }
                    )

                res["member_list"] = member_list
                return json.dumps(res)

        except Exception as e:
            _logger.error("Error occurred during member submit: %s", e)
            return json.dumps({"error": "Failed to update member details"})

    ############### Controller for Individual Creation ################

    @http.route("/portal/registration/individual", type="http", auth="user", website=True)
    def individual_list(self, **kw):
        user = request.env.user

        individual = (
            request.env["res.partner"]
            .sudo()
            .search(
                [
                    ("active", "=", True),
                    ("is_registrant", "=", True),
                    ("is_group", "=", False),
                    ("user_id", "=", user.id),
                ]
            )
        )
        return request.render("g2p_registration_portal_base.individual_list", {"individual": individual})

    @http.route(
        ["/portal/registration/individual/create/"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def individual_registrar_create(self, **kw):
        gender = request.env["gender.type"].sudo().search([])
        return request.render(
            "g2p_registration_portal_base.individual_registrant_form_template",
            {"gender": gender},
        )

    @http.route(
        ["/portal/registration/individual/create/submit"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def individual_create_submit(self, **kw):
        user = request.env.user

        try:
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

            request.env["res.partner"].sudo().create(
                {
                    "given_name": kw.get("given_name"),
                    "addl_name": kw.get("addl_name"),
                    "family_name": kw.get("family_name"),
                    "name": name,
                    "birthdate": birthdate,
                    "gender": kw.get("gender"),
                    "email": kw.get("email"),
                    "user_id": user.id,
                    "is_registrant": True,
                    "is_group": False,
                }
            )
            return request.redirect("/portal/registration/individual")

        except Exception as e:
            _logger.error("Error occurred%s" % e)
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "An error occurred. Please try again later."},
            )

    @http.route(
        ["/portal/registration/individual/update/<int:_id>"],
        type="http",
        auth="user",
        website=True,
        csrf=False,
    )
    def indvidual_update(self, _id, **kw):
        try:
            gender = request.env["gender.type"].sudo().search([])
            beneficiary = request.env["res.partner"].sudo().browse(_id)
            if not beneficiary:
                return request.render(
                    "g2p_registration_portal_base.error_template",
                    {"error_message": "Beneficiary not found."},
                )

            return request.render(
                "g2p_registration_portal_base.individual_update_form_template",
                {
                    "beneficiary": beneficiary,
                    "gender": gender,
                },
            )
        except Exception:
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "Invalid URL."},
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
                    }
                )
            return request.redirect("/portal/registration/individual")

        except Exception as e:
            _logger.error("Error occurred%s" % e)
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "An error occurred. Please try again later."},
            )
