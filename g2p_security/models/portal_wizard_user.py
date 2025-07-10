from odoo import models


class PortalWizardUser(models.TransientModel):
    _inherit = "portal.wizard.user"

    def action_grant_access(self):
        res = super().action_grant_access()
        for wizard_user in self:
            user = wizard_user.user_id.sudo()
            if user and wizard_user.partner_id.portal_password:
                user.write({"password": wizard_user.partner_id.portal_password})
        return res
