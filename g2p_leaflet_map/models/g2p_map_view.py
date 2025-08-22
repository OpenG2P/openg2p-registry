from odoo import models


class G2PMapView(models.Model):
    _name = "g2p.map.view"
    _description = "Map View"


class ResPartnerMap(models.Model):
    _inherit = "res.partner"

    def show_map(self):
        self.ensure_one()

        action = {
            "type": "ir.actions.act_window",
            "name": "Partner Map",
            "res_model": "g2p.map.view",
            "view_mode": "lmap",
            "view_id": self.env.ref("g2p_leaflet_map.g2p_map_view_id").id,
            "target": "new",
            "context": {
                "partner_latitiude": self.partner_latitude,
                "partner_longitude": self.partner_longitude,
            },
        }
        return action
