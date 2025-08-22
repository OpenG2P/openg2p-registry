from odoo import fields, models


class OSMConfig(models.Model):
    _name = "g2p.osm.config"
    _description = "OSM Configuration"

    tile_server_url = fields.Char(default="https://tile.openstreetmap.org/{z}/{x}/{y}.png")
