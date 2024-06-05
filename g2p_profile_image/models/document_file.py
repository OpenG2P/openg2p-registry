from odoo import api, fields, models
from odoo.exceptions import UserError


class G2PDocumentFile(models.Model):
    _inherit = "storage.file"
    def create(self,vals):
        if type(vals) is dict:
            self._check_profile_tag(vals)
        elif type(vals) is list:
            for i in range(len(vals)):
                vals_obj = vals[i]
                self._check_profile_tag(vals_obj)

        
            
        return super(G2PDocumentFile,self).create(vals)

    def _check_profile_tag(self, vals_obj):
        profile_tag = self.env['g2p.document.tag'].get_tag_by_name('Profile Image')
        profile_tag_id = profile_tag.id
        tags_ids = vals_obj.get('tags_ids', [])
        has_profile_tag = any(tag[1] == profile_tag_id for tag in tags_ids)

        if has_profile_tag:
            existing_file = self.search([
                ('registrant_id', '=', vals_obj.get('registrant_id')),
                ('tags_ids', 'in', [profile_tag.id])
            ], limit=1)
            
            if existing_file:
                raise UserError("Profile image already exists. To change your profile picture, hover over your current image and click the edit button.")