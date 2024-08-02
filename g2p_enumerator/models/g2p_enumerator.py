from odoo import fields, models


class G2PEnumerator(models.Model):
    _name = "g2p.enumerator"

    #Enum Details
    enumerator_name = fields.Char()
    enumerator_id = fields.Char()
    data_collection_date = fields.Date()

    #Location
    enum_latitude = fields.Float(string="Latitude", digits=(10, 7))
    enum_longitude = fields.Float(string="Longitude", digits=(10, 7))
    enum_altitude = fields.Float(string="Altitude")
    enum_accuracy = fields.Float(string="Accuracy")

    partner_id = fields.Many2one("res.partner")

