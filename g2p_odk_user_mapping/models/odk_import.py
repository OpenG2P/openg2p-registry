from datetime import datetime

from odoo import models


class OdkImport(models.Model):
    _inherit = "odk.import"

    def process_records_handle_enumerator_info(self, mapped_json, member):
        """Processes records from ODK and assigns odk_app_user_id"""
        submitter_id = str(member.get("__system", {}).get("submitterId"))
        submission_date_str = member.get("__system", {}).get("submissionDate")
        submission_date = datetime.strptime(submission_date_str, "%Y-%m-%dT%H:%M:%S.%fZ").date()

        odk_user = self.env["odk.app.user"].search(
            [("odk_config_id", "=", self.odk_config.id), ("odk_user_id", "=", submitter_id)], limit=1
        )

        if odk_user:
            user = self.env["res.users"].search(
                [("odk_config_id", "=", self.odk_config.id), ("odk_app_user", "=", odk_user.id)]
            )
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

                # Temporarily store enumerator details to pass down to group members
                mapped_json["enumerator_user"] = user
                mapped_json["enumerator_submission_date"] = submission_date

    def get_enumerator_info(self, mapped_json, individual_data):
        """Assigns odk_app_user_id and enumerator details for group members."""
        if individual_data:
            enumerator_user = mapped_json.get("enumerator_user")
            enumerator_submission_date = mapped_json.get("enumerator_submission_date")
            if enumerator_user:
                enumerator = self.env["g2p.enumerator"].create(
                    {
                        "name": enumerator_user.name,
                        "enumerator_user_id": str(enumerator_user.id),
                        "data_collection_date": enumerator_submission_date,
                    }
                )
                individual_data.update(
                    {
                        "enumerator_id": enumerator.id,
                        "creator_eid": enumerator_user.partner_id.eid,
                    }
                )

    def cleanup_enumerator_metadata(self, mapped_json):
        """Removes temporary enumerator details that were used during processing"""
        if "enumerator_user" in mapped_json:
            mapped_json.pop("enumerator_user")
            mapped_json.pop("enumerator_submission_date")
