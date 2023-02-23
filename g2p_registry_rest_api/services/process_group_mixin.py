from odoo.addons.component.core import AbstractComponent


class ProcessGroupMixin(AbstractComponent):
    _name = "process_group.rest.mixin"
    _inherit = "process_individual.rest.mixin"
    _description = """
        Process Group REST API Mixin
    """

    def _process_group(self, group_info):
        grp_rec = {
            "name": group_info.name,
            "registration_date": group_info.registration_date,
            "is_registrant": True,
            "is_group": True,
            "email": group_info.email,
            "address": group_info.address,
            "is_partial_group": group_info.is_partial_group,
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
        ids = self._process_ids(ids_info)
        if ids:
            grp_rec.update({"reg_ids": ids})

        phone_numbers = []
        phone_numbers, primary_phone = self._process_phones(ids_info)
        if primary_phone:
            grp_rec.update({"phone": primary_phone})
        if phone_numbers:
            grp_rec.update({"phone_number_ids": phone_numbers})

        return grp_rec
