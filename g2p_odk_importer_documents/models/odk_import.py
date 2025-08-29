import base64

from odoo import fields, models


class OdkImport(models.Model):
    _inherit = "odk.import"

    storage_backend_id = fields.Many2one("storage.backend", string="Storage Backend")

    def process_records_handle_media_import(self, mapped_json, member):
        """Image import is handled by super module.
        Supporting documents import is handled here.
        The jq_format and the final mapped_json should look like this:
        {
            image_1920: .form_field_photo,
            supporting_document_ids: [
                {tags_ids: ["ID Proof", "Address Proof"], data: .form_field_id_proof},
                {tags_ids: ["Land Ownership"], data: .form_field_land_ownership}
            ]
        }
        This translates to:
        {
            "image_1920": "/potato/my_pic.jpg",
            supporting_document_ids: [
                {"tags_ids": ["ID Proof", "Address Proof"], "data": "/tomato/id_card.pdf"},
                {"tags_ids": ["Land Ownership"], "data": "/radish/land_deed.pdf"}
            ]
        }
        Recommended to not use "name" field of supporting document object. Instead
        use tags as shown above. Random ID gets generated in place of name.
        """
        res = super().process_records_handle_media_import(mapped_json, member)
        instance_id = member.get("meta", {}).get("instanceID")
        if not instance_id:
            return res

        default_storage_backend_id = self.storage_backend_id
        if not default_storage_backend_id:
            default_storage_backend_id = self.env["res.partner"].get_registry_documents_store()
        if default_storage_backend_id:
            default_storage_backend_id = default_storage_backend_id.id

        DOC_TAGS = self.env["g2p.document.tag"].sudo()

        supporting_docs = []

        for doc_mapping in mapped_json.get("supporting_documents_ids", []):
            filename = doc_mapping.get("data")
            tags = doc_mapping.get("tags_ids", [])

            attachm = None
            if filename:
                attachm = self.odk_config.download_attachment(instance_id, filename)
            else:
                continue

            storage_backend_id = doc_mapping.get("backend_id", default_storage_backend_id)

            doc_file = {
                "backend_id": storage_backend_id,
                "tags_ids": [(4, DOC_TAGS.get_or_create_tag_from_name(tag).id) for tag in tags],
                "data": base64.b64encode(attachm).decode("utf-8") if attachm else None,
            }
            if doc_mapping.get("name"):
                doc_file["name"] = doc_mapping["name"]

            supporting_docs.append((0, 0, doc_file))
        mapped_json["supporting_documents_ids"] = supporting_docs
