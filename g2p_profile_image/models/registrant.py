from odoo import models

from odoo.addons.g2p_document_field.image_field import DocumentImageField


class RegistramtWithProfileImage(models.Model):
    _inherit = "res.partner"

    image_1920 = DocumentImageField(
        documents_field="supporting_documents_ids",
        get_tags_func="_profile_image_get_tags_func",
        get_storage_backend_func="_profile_image_get_sb_func",
        max_width=1920,
        max_height=1920,
    )

    def _profile_image_get_tags_func(self):
        return self.env.ref("g2p_profile_image.document_tag_profile_image")

    def _profile_image_get_sb_func(self):
        IR_CONFIG = self.env["ir.config_parameter"].sudo()
        image_doc_store = IR_CONFIG.get_param("g2p_profile_image.image_document_storage")
        if image_doc_store:
            return self.env["storage.backend"].browse(int(image_doc_store))
        return self.get_registry_documents_store()
