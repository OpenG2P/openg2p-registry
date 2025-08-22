from odoo import models


class OdkImport(models.Model):
    _inherit = "odk.import"

    def process_records_handle_addl_data(self, mapped_json):
        res = super().process_records_handle_addl_data(mapped_json)
        # Perform additional computation with the fields
        # and update back the original mapped_json
        mapped_json.update(
            {
                "education_level": mapped_json.get("education_level", None),
                "employment_status": mapped_json.get("employment_status", None),
                "marital_status": mapped_json.get("marital_status", None),
            }
        )
        return res

    # def patched_member_relationship(self, source_id, record):
    #     print(record)
    #     relation = self.env["g2p.relationship"].search(
    #         [("name", "=", record.get("household_member").get("relationship_with_household_head"))], limit=1
    #     )
    #     print('--- relation', relation)

    #     if relation and source_id:
    #         return {"source": source_id, "relation": relation.id, "start_date": datetime.now()}

    #     return None
