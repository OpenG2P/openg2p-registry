import json

from odoo.addons.component.core import AbstractComponent


class GroupApiHelper(AbstractComponent):
    _name = "registrant_group.rest.service.helper"

    def _get(self, _id):
        partner = self.env["res.partner"].browse(_id)
        if partner and partner.is_group:
            return partner
        return None

    def process_group(self, group_info):
        grp_rec = {
            "name": group_info.name,
            "registration_date": group_info.registration_date,
            "is_registrant": True,
            "is_group": True,
            "email": group_info.email,
            "address": group_info.address,
            "is_partial_group": group_info.is_partial_group,
            "additional_g2p_info": json.dumps(
                group_info.addl_info, separators=(",", ":")
            ),
        }
        # Add group's kind field
        if group_info.kind:
            # Search Kind
            kind_id = self.env["g2p.group.kind"].search(
                [("name", "=", group_info.kind)]
            )
            if kind_id:
                kind_id = kind_id[0]
            else:
                # Create a new Kind
                kind_id = self.env["g2p.group.kind"].create({"name": group_info.kind})
                kind_id = kind_id
            grp_rec.update({"kind": kind_id.id})

        ids = []
        ids_info = group_info
        indv_helper = self.env["registrant_individual.rest.service.helper"]
        ids = indv_helper.process_ids(ids_info)
        if ids:
            grp_rec.update({"reg_ids": ids})

        phone_numbers = []
        phone_numbers, primary_phone = indv_helper.process_phones(ids_info)
        if primary_phone:
            grp_rec.update({"phone": primary_phone})
        if phone_numbers:
            grp_rec.update({"phone_number_ids": phone_numbers})

        return grp_rec
