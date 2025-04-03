from datetime import datetime

import jq

from odoo import _, models
from odoo.exceptions import UserError, ValidationError


class OdkImport(models.Model):
    _inherit = "odk.import"

    def process_records(self, instance_id=None, last_sync_time=None):
        """Processes records from ODK and assigns odk_app_user_id efficiently."""
        self.ensure_one()

        if not self.odk_config:
            raise UserError(_("Please configure the ODK."))

        data = self.odk_config.download_records(instance_id=instance_id, last_sync_time=last_sync_time)
        partner_count = 0

        odk_app_users = self.env["odk.app.user"].search([("odk_config_id", "=", self.odk_config.id)])
        users = self.env["res.users"].search([("odk_config_id", "=", self.odk_config.id)])

        odk_app_user_dict = {str(user.odk_user_id): user.id for user in odk_app_users}
        user_dict = {int(user.odk_app_user.id): user for user in users}

        for member in data["value"]:
            mapped_json = jq.first(self.json_formatter, member)

            if self.target_registry == "individual":
                mapped_json.update({"is_registrant": True, "is_group": False})
            elif self.target_registry == "group":
                mapped_json.update({"is_registrant": True, "is_group": True})

            submitter_id = str(member.get("__system", {}).get("submitterId"))
            submission_date_str = member.get("__system", {}).get("submissionDate")
            submission_date = datetime.strptime(submission_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()

            if submitter_id:
                odk_app_user_id = odk_app_user_dict.get(submitter_id)
                user = user_dict.get(odk_app_user_id)
                if user:
                    enumerator = self.env["g2p.enumerator"].create(
                        {
                            "name": user.name,
                            "enumerator_user_id": str(user.id),
                            "data_collection_date": submission_date,
                        }
                    )
                    mapped_json["enumerator_id"] = enumerator.id
                    mapped_json["creator_eid"] = user.partner_id.eid
                    mapped_json["enumerator_user"] = user
                    mapped_json["enumerator_submission_date"] = submission_date

            self.process_records_handle_one2many_fields(mapped_json)
            self.process_records_handle_media_import(mapped_json, member)
            self.process_records_handle_many2one_fields(mapped_json)
            self.process_records_handle_addl_data(mapped_json)

            if "enumerator_user" in mapped_json:
                mapped_json.pop("enumerator_user")
                mapped_json.pop("enumerator_submission_date")

            self.env["res.partner"].sudo().create(mapped_json)
            partner_count += 1
            data.update({"form_updated": True})

        data.update({"partner_count": partner_count})

        return data

    def process_records_handle_one2many_fields(self, mapped_json):
        self.ensure_one()

        if "phone_number_ids" in mapped_json:
            mapped_json["phone_number_ids"] = [
                (
                    0,
                    0,
                    {
                        "phone_no": phone.get("phone_no"),
                        "date_collected": phone.get("date_collected"),
                        "disabled": phone.get("disabled"),
                    },
                )
                for phone in mapped_json["phone_number_ids"]
            ]

        if "group_membership_ids" in mapped_json and self.target_registry == "group":
            individual_ids = []
            relationships_ids = []
            group_membership_data = (
                mapped_json.get("group_membership_ids")
                if mapped_json.get("group_membership_ids") is not None
                else []
            )

            enumerator_user = mapped_json.get("enumerator_user")
            enumerator_submission_date = mapped_json.get("enumerator_submission_date")

            for individual_mem in group_membership_data:
                individual_data = self.get_individual_data(individual_mem)
                individual = self.env["res.partner"].sudo().create(individual_data)
                if individual:
                    if enumerator_user:
                        enumerator = self.env["g2p.enumerator"].create(
                            {
                                "name": enumerator_user.name,
                                "enumerator_user_id": str(enumerator_user.id),
                                "data_collection_date": enumerator_submission_date,
                            }
                        )
                        individual.write(
                            {
                                "enumerator_id": enumerator.id,
                                "creator_eid": enumerator_user.partner_id.eid,
                            }
                        )

                    kind = self.get_member_kind(individual_mem)
                    individual_data = {"individual": individual.id}
                    if kind:
                        individual_data["kind"] = [(4, kind.id)]
                    relationship = self.get_member_relationship(individual.id, individual_mem)
                    if relationship:
                        relationships_ids.append((0, 0, relationship))
                    individual_ids.append((0, 0, individual_data))
            mapped_json["related_1_ids"] = relationships_ids
            mapped_json["group_membership_ids"] = individual_ids

        if "reg_ids" in mapped_json:
            reg_ids = mapped_json["reg_ids"]
            mapped_json["reg_ids"] = []
            for reg_id in reg_ids:
                id_type = self.env["g2p.id.type"].search([("name", "=", reg_id.get("id_type"))], limit=1)
                if not id_type:
                    raise ValidationError(
                        f"ID Type not found while handling Reg IDs. {reg_id.get('id_type')}"
                    )
                mapped_json["reg_ids"].append(
                    (
                        0,
                        0,
                        {
                            "id_type": id_type.id,
                            "value": reg_id.get("value"),
                            "expiry_date": reg_id.get("expiry_date"),
                            "status": reg_id.get("status"),
                        },
                    )
                )
