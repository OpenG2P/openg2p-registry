import json
import logging
from datetime import date

from odoo import http
from odoo.http import request

from odoo.addons.g2p_agent_portal_base.controllers.main import AgentPortalBase

_logger = logging.getLogger(__name__)


class G2PregistrationPortalBase(AgentPortalBase):
    ################################################################################
    #                      Controllers for Household Creation,                     #
    #                        Submission, and Update                                #
    ################################################################################

    @http.route("/portal/registration/group", type="http", auth="user")
    def group_list(self, **kw):
        self.check_roles("Agent")
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
        csrf=False,
    )
    def group_create(self, **kw):
        self.check_roles("Agent")
        gender = request.env["gender.type"].sudo().search([])

        return request.render(
            "g2p_registration_portal_base.group_create_form_template",
            {"gender": gender},
        )

    @http.route(
        ["/portal/registration/group/create/submit"],
        type="http",
        auth="user",
        csrf=False,
    )
    def group_create_submit(self, **kw):
        self.check_roles("Agent")
        try:
            head_name = kw.get("name")
            beneficiary_id = None
            if kw.get("group_id"):
                beneficiary_id = request.env["res.partner"].sudo().browse(int(kw.get("group_id"))).id
            else:
                if head_name:
                    user = request.env.user

                    data = {
                        "name": head_name,
                        "is_registrant": True,
                        "is_group": True,
                        "birthdate": kw.get("birthdate"),
                        "email": kw.get("email"),
                        "address": kw.get("address"),
                        "gender": kw.get("gender"),
                        "user_id": user.id,
                    }

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
            _logger.error("Error occurred%s" % e)
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "An error occurred. Please try again later."},
            )

    @http.route(
        ["/portal/registration/group/update/<int:_id>"],
        type="http",
        auth="user",
        csrf=False,
    )
    def group_update(self, _id, **kw):
        self.check_roles("Agent")
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
        csrf=False,
    )
    def group_submit(self, **kw):
        self.check_roles("Agent")
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

    ################################################################################
    #                      Controllers for Member Creation,                        #
    #                        Submission, and Update                                #
    ################################################################################

    @http.route(
        ["/portal/registration/member/create/"],
        type="http",
        auth="user",
        csrf=False,
    )
    def individual_create(self, **kw):
        self.check_roles("Agent")
        res = dict()
        try:
            user = request.env.user
            head_name = kw.get("Household_name")
            head_individual = None

            if kw.get("group_id"):
                group_rec = request.env["res.partner"].sudo().browse(int(kw.get("group_id")))
            else:
                if head_name:
                    group_rec = (
                        request.env["res.partner"]
                        .sudo()
                        .create(
                            {
                                "name": head_name,
                                "is_registrant": True,
                                "is_group": True,
                                "user_id": user.id,
                            }
                        )
                    )

                    head_name_parts = head_name.split(" ")
                    h_given_name = head_name_parts[0]

                    h_family_name = head_name_parts[-1]

                    if len(head_name_parts) > 2:
                        h_addl_name = " ".join(head_name_parts[1:-1])
                    else:
                        h_addl_name = ""

                    name = f"{h_family_name} , {h_given_name} {h_addl_name}"

                    head_individual = (
                        request.env["res.partner"]
                        .sudo()
                        .create(
                            {
                                "name": name,
                                "given_name": h_given_name,
                                "addl_name": h_addl_name,
                                "family_name": h_family_name,
                                "birthdate": kw.get("Household_dob"),
                                "gender": kw.get("Household_gender"),
                                "email": kw.get("Household_email"),
                                "address": kw.get("Household_address"),
                                "is_registrant": True,
                                "is_group": False,
                                "user_id": user.id,
                            }
                        )
                    )

            given_name = kw.get("given_name")
            family_name = kw.get("family_name")
            addl_name = kw.get("addl_name")

            name = f"{family_name}, {given_name} {addl_name}"

            partner_data = {
                "name": name,
                "given_name": given_name,
                "addl_name": addl_name,
                "family_name": family_name,
                "birthdate": kw.get("dob"),
                "gender": kw.get("gender"),
                "email": kw.get("email"),
                "address": kw.get("address"),
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
                age = 0
                dob = membership.individual.birthdate
                if dob:
                    today = date.today()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

                member_list.append(
                    {
                        "id": membership.individual.id,
                        "name": membership.individual.name,
                        "age": age,
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
        csrf=False,
    )
    def update_member(self, **kw):
        self.check_roles("Agent")
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
                    "email": beneficiary.email,
                    "address": beneficiary.address,
                    "id": beneficiary.id,
                }
                return json.dumps(exist_value)

        except Exception as e:
            _logger.error("ERROR LOG IN UPDATE MEMBER%s", e)

    @http.route(
        "/portal/registration/member/update/submit/",
        type="http",
        auth="user",
        csrf=False,
    )
    def update_member_submit(self, **kw):
        self.check_roles("Agent")
        try:
            member = request.env["res.partner"].sudo().browse(int(kw.get("member_id")))
            res = dict()
            if member:
                given_name = kw.get("given_name")
                family_name = kw.get("family_name")
                addl_name = kw.get("addl_name")

                name = f"{family_name}, {given_name} {addl_name}"

                member.sudo().write(
                    {
                        "name": name,
                        "given_name": given_name,
                        "addl_name": addl_name,
                        "family_name": family_name,
                        "birthdate": kw.get("birthdate"),
                        "gender": kw.get("gender"),
                        "email": kw.get("email"),
                        "address": kw.get("address"),
                    }
                )

                member_list = []

                for membership in member:
                    age = 0
                    dob = membership.birthdate
                    if dob:
                        today = date.today()
                        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

                    member_list.append(
                        {
                            "id": membership.id,
                            "name": membership.name,
                            "age": age,
                            "gender": membership.gender,
                            "active": membership.active,
                        }
                    )

                res["member_list"] = member_list
                return json.dumps(res)

        except Exception as e:
            _logger.error("Error occurred during member submit: %s", e)
            return json.dumps({"error": "Failed to update member details"})

    ################################################################################
    #                      Controllers for Individual Creation,                   #
    #                        Submission, and Update                               #
    ################################################################################

    @http.route("/portal/registration/individual", type="http", auth="user")
    def individual_list(self, **kw):
        self.check_roles("Agent")
        user = request.env.user

        domain = [
            ("active", "=", True),
            ("is_registrant", "=", True),
            ("is_group", "=", False),
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

        individual = request.env["res.partner"].sudo().search(domain)

        return request.render("g2p_registration_portal_base.individual_list", {"individual": individual})

    @http.route(
        ["/portal/registration/individual/create/"],
        type="http",
        auth="user",
        csrf=False,
    )
    def individual_registrar_create(self, **kw):
        self.check_roles("Agent")
        gender = request.env["gender.type"].sudo().search([])
        return request.render(
            "g2p_registration_portal_base.individual_registrant_form_template",
            {"gender": gender},
        )

    @http.route(
        ["/portal/registration/individual/create/submit"],
        type="http",
        auth="user",
        csrf=False,
    )
    def individual_create_submit(self, **kw):
        self.check_roles("Agent")
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
                    "name": name,
                    "given_name": kw.get("given_name"),
                    "addl_name": kw.get("addl_name"),
                    "family_name": kw.get("family_name"),
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
        csrf=False,
    )
    def indvidual_update(self, _id, **kw):
        self.check_roles("Agent")
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
        csrf=False,
    )
    def update_individual_submit(self, **kw):
        self.check_roles("Agent")
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

                member = member.sudo().write(
                    {
                        "name": name,
                        "given_name": kw.get("given_name"),
                        "addl_name": kw.get("addl_name"),
                        "family_name": kw.get("family_name"),
                        "birthdate": birthdate,
                        "gender": kw.get("gender"),
                        "email": kw.get("email"),
                        "address": kw.get("address"),
                    }
                )

            return request.redirect("/portal/registration/individual")

        except Exception as e:
            _logger.error("Error occurred%s" % e)
            return request.render(
                "g2p_registration_portal_base.error_template",
                {"error_message": "An error occurred. Please try again later."},
            )
