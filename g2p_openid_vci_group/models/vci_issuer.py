import logging
import uuid
from datetime import datetime

import jq

from odoo import fields, models

from odoo.addons.g2p_openid_vci.json_encoder import VCJSONEncoder

_logger = logging.getLogger(__name__)


class OpenIDVCIssuerGroup(models.Model):
    _inherit = "g2p.openid.vci.issuers"

    issuer_type = fields.Selection(
        selection_add=[
            (
                "Registry_Group",
                "Registry Group",
            )
        ],
        ondelete={"Registry_Group": "cascade"},
    )

    def issue_vc_Registry_Group(self, auth_claims, credential_request):
        self.ensure_one()
        web_base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url").rstrip("/")
        reg_id = (
            self.env["g2p.reg.id"]
            .sudo()
            .search(
                [
                    ("id_type", "=", self.auth_sub_id_type_id.id),
                    ("value", "=", auth_claims["sub"]),
                ],
                limit=1,
            )
        )
        if not reg_id:
            raise ValueError("ID not found in DB. Invalid Subject Received in auth claims")

        head_kind = self.env.ref("g2p_registry_membership.group_membership_kind_head")
        # Searches for the first group which in the individual is a HEAD.
        individual_group_membership = (
            self.env["g2p.group.membership"]
            .sudo()
            .search(
                [
                    ("individual", "=", reg_id.partner_id.id),
                    ("kind", "=", head_kind.id),
                ],
                limit=1,
            )
        )
        if not individual_group_membership:
            raise ValueError("Individual is not head of any group.")

        group = individual_group_membership.group
        group_dict = group.read()[0]
        group_dict["reg_ids"] = {reg_id.id_type.name: reg_id.read()[0] for reg_id in group.reg_ids}
        group_dict["image"] = self.get_image_base64_data_in_url((group.image_1920 or b"").decode())
        group_dict["address"] = self.get_full_address(group.address)

        group_member_individuals = group.group_membership_ids.individual
        group_memberships_dict = group.group_membership_ids.read()
        group_member_individuals_dict = group_member_individuals.read()
        for i, membership in enumerate(group_memberships_dict):
            membership["individual"] = group_member_individuals_dict[i]
            membership["individual"]["reg_ids"] = {
                reg_id.id_type.name: reg_id.read()[0] for reg_id in group_member_individuals[i].reg_ids
            }
            membership["individual"]["image"] = self.get_image_base64_data_in_url(
                (group_member_individuals[i].image_1920 or b"").decode()
            )
            membership["individual"]["address"] = self.get_full_address(group_member_individuals[i].address)

        head_member_dict = None
        for i, membership in enumerate(group_memberships_dict):
            if str(membership["id"]) == str(individual_group_membership.id):
                head_member_dict = membership
                group_memberships_dict.pop(i)
                break

        group_dict["members"] = group_memberships_dict
        group_dict["head"] = head_member_dict
        _logger.info("VC Group: Details gathered. Generating credential.")

        curr_datetime = f'{datetime.now().isoformat(timespec = "milliseconds")}Z'
        credential = jq.first(
            self.credential_format,
            VCJSONEncoder.python_dict_to_json_dict(
                {
                    "vc_id": str(uuid.uuid4()),
                    "web_base_url": web_base_url,
                    "issuer": self.read()[0],
                    "curr_datetime": curr_datetime,
                    "group": group_dict,
                },
            ),
        )

        credential_response = {
            "credential": self.sign_and_issue_credential(credential),
            "format": credential_request["format"],
        }
        return credential_response

    def set_default_credential_type_Registry_Group(self):
        self.credential_type = "OpenG2PRegistryGroupVerifiableCredential"

    def set_from_static_file_Registry_Group(self, **kwargs):
        kwargs.setdefault("module_name", "g2p_openid_vci_group")
        return self.set_from_static_file_Registry(**kwargs)
