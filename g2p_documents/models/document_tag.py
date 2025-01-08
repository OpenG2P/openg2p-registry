from odoo import api, fields, models


class G2PDocumentTags(models.Model):
    _name = "g2p.document.tag"
    _description = "G2P Document Tag"
    _order = "id asc"

    name = fields.Char(required=True, index=True)

    _sql_constraints = [
        (
            "name_unique",
            "unique (name)",
            "Name of the tag should be unique",
        ),
    ]

    @api.model
    def get_or_create_tag_from_name(self, tag_name, **kwargs):
        res = self.search([("name", "=", tag_name)], **kwargs)
        if res:
            return res[0]
        return self.create({"name": tag_name})
