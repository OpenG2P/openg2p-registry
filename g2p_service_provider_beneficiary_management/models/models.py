# from odoo import models, fields, api


# class g2p_service_provider_beneficiary_management(models.Model):
#     _name = 'g2p_service_provider_beneficiary_management.g2p_service_provider_beneficiary_management'
#     _description = 'g2p_service_provider_beneficiary_management.g2p_service_provider_beneficiary_management'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
