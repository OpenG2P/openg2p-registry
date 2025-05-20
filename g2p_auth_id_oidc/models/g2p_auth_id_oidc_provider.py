import logging
from datetime import datetime

from odoo import fields, models

_logger = logging.getLogger(__name__)


class G2PAuthIDOidcProvider(models.Model):
    _inherit = "auth.oauth.provider"

    g2p_id_type = fields.Many2one("g2p.id.type", "G2P Registrant ID Type", required=False)

    def oidc_signin_find_existing_partner(self, validation, params):
        if self.g2p_id_type:
            user_id = validation.get("user_id")
            # TODO: Handle expired IDs
            reg_id = self.env["g2p.reg.id"].search(
                [("id_type", "=", self.g2p_id_type.id), ("value", "=", user_id)]
            )
            if reg_id:
                return reg_id.partner_id
        return None

    def oidc_signin_process_name(self, validation, params, **kw):
        super().oidc_signin_process_name(validation, params, **kw)
        if self.g2p_id_type:
            name_arr = validation.get("name", "").split(" ")
            given_name = name_arr[0]
            family_name = name_arr[-1]
            addl_name = " ".join(name_arr[1:-1])

            name = family_name
            if given_name:
                name += ", " + given_name
            if addl_name:
                name += " " + addl_name

            validation["given_name"] = given_name
            validation["family_name"] = family_name
            validation["addl_name"] = addl_name
            validation["name"] = name.upper()
        return validation

    def oidc_signin_process_reg_ids(self, validation, params, oauth_partner=None, **kw):
        if self.g2p_id_type:
            reg_ids = []
            for key, value in validation.items():
                if key.startswith("user_id"):
                    id_type_id = key.removeprefix("user_id")
                    if not id_type_id:
                        id_type_id = self.g2p_id_type.id
                    else:
                        try:
                            id_type_id = int(id_type_id)
                        except Exception:
                            _logger.exception("Invalid Id type mapping. Has to end with `user_id<int>`")
                            continue
                    append = True
                    if oauth_partner:
                        for reg_id in oauth_partner.reg_ids:
                            if reg_id.id_type.id == id_type_id:
                                reg_ids.append(
                                    (
                                        1,
                                        reg_id.id,
                                        {
                                            "value": value,
                                            "authentication_status": "authenticated",
                                            "last_authentication_time": datetime.now(),
                                        },
                                    )
                                )
                                append = False
                                break
                    if append:
                        reg_ids.append(
                            (
                                0,
                                0,
                                {
                                    "id_type": id_type_id,
                                    "value": value,
                                    "expiry_date": None,  # TODO: Set expiry date from config/validation
                                },
                            )
                        )
            validation["reg_ids"] = reg_ids
        return validation

    def oidc_signin_process_phone(self, validation, params, oauth_partner=None, **kw):
        super().oidc_signin_process_phone(validation, params, oauth_partner=oauth_partner, **kw)
        if self.g2p_id_type:
            phone = validation.get("phone", "")
            phone_numbers = []
            if phone:
                append = True
                if oauth_partner:
                    for phone_num in oauth_partner.phone_number_ids:
                        if phone_num.phone_no == phone:  # TODO: Check without country code
                            validation.pop("phone")
                            append = False
                            break
                if append:
                    phone_numbers.append(
                        (
                            0,
                            0,
                            {
                                "phone_no": phone,
                            },
                        )
                    )
            validation["phone_number_ids"] = phone_numbers
        return validation

    def oidc_signin_process_other_fields(self, validation, params, **kw):
        self.oidc_signin_process_reg_ids(validation, params, **kw)
        if self.g2p_id_type:
            validation["is_registrant"] = True
            validation["is_group"] = False
        super().oidc_signin_process_other_fields(validation, params, **kw)
        return validation
