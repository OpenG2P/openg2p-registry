from odoo import api, fields, models


class G2PDocumentTags(models.Model):
    _name = "g2p.document.tag"
    _description = "G2P Document Tag"
    _order = "id asc"

    name = fields.Char()

    _sql_constraints = [
        (
            "name_unique",
            "unique (name)",
            "Name of the tag should be unique",
        ),
    ]

    @api.model
    def get_tag_by_name(self, name, **kwargs):
        res = self.search([("name", "=", name)], **kwargs)
        if res:
            return res[0]
        return None
