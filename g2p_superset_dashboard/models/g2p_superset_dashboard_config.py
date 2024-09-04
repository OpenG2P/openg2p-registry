import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SupersetDashboardConfig(models.Model):
    _name = "g2p.superset.dashboard.config"
    _description = "Superset Dashboard Configuration"

    name = fields.Char(string="Dashboard Name", required=True)
    url = fields.Char(string="Dashboard URL", required=True)
    access_user_ids = fields.Many2many(
        "res.users",
        string="Access Rights",
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.create_menus()
        return records

    def write(self, vals):
        res = super().write(vals)
        self.create_menus()
        return res

    def unlink(self):
        res = super().unlink()
        self.create_menus()
        return res

    @api.model
    def create_menus(self):
        existing_menus = self.env["ir.ui.menu"].search(
            [("parent_id", "=", self.env.ref("g2p_superset_dashboard.menu_superset_dashboard_embedded").id)]
        )
        existing_menus.unlink()

        user = self.env.user
        dashboards = self.search([("access_user_ids", "in", user.id)])
        # dashboards = self.search([])
        for dashboard in dashboards:
            self.env["ir.actions.client"].create(
                {
                    "name": dashboard.name,
                    "tag": "g2p.superset_dashboard_embedded",
                    "context": {"url": dashboard.url},
                }
            )

            # menu_item = self.env['ir.ui.menu'].create({
            #     'name': dashboard.name,
            #     'parent_id': self.env.ref('g2p_superset_dashboard.menu_superset_dashboard_embedded').id,
            #     'action': f"ir.actions.client,{action.id}",
            # })
