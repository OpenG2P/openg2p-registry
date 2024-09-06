import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SupersetDashboardConfig(models.Model):
    _name = "g2p.superset.dashboard.config"
    _description = "Superset Dashboard Configuration"

    name = fields.Char(string="Dashboard Name", required=True)
    url = fields.Char(string="Dashboard URL", required=True)
    access_user_ids = fields.Many2many("res.users", string="Access Rights")


# ***  USE CODE BELOW TO EMBED SUPERSET DASHBOARD IN ODOO MENUITEMS. ***
# THIS MAY SLOW PERFORMANCE OF ODOO SINCE IT WILL BE CREATING MENUITEMS AND ACTIONS FOR EACH DASHBOARDS.


# Override create method to regenerate menus when new dashboards are created.s
# @api.model_create_multi
# def create(self, vals_list):
#     records = super().create(vals_list)
#     self._create_or_update_menus(records)
#     return records

# # Override write method to regenerate menus when dashboards are updated.
# def write(self, vals):
#     res = super().write(vals)
#     self._create_or_update_menus(self)
#     return res

# # Override unlink method to delete menus related to the dashboards being deleted.
# def unlink(self):
#     dashboard_names = self.mapped("name")
#     res = super().unlink()
#     self._delete_menus(dashboard_names)
#     return res

# # Create or update the menus for the provided dashboards.
# def _create_or_update_menus(self, dashboards):
#     try:
# for dashboard in dashboards:
#     existing_menu = self.env["ir.ui.menu"].search([
#         ("parent_id", "=", self.env.ref(
#             "g2p_superset_dashboard.menu_superset_dashboard_embedded").id),
#         ("name", "=", dashboard.name)
#     ])
#     existing_menu.unlink()

#             action = self.env["ir.actions.client"].create({
#                 "name": dashboard.name,
#                 "tag": "g2p_superset_dashboard_embedded",
#                 "context": {"url": dashboard.url},
#             })

# self.env["ir.ui.menu"].create({
#     "name": dashboard.name,
#     "parent_id": self.env.ref(
#           "g2p_superset_dashboard.menu_superset_dashboard_embedded").id,
#     "action": f"ir.actions.client,{action.id}",
# })

#             _logger.info(f"Menu for dashboard '{dashboard.name}' created/updated successfully.")
#     except Exception as e:
#         _logger.error(f"Error while creating/updating menus: {e}")
#         raise

# # Delete the menus associated with the dashboards being deleted.
# # def _delete_menus(self, dashboard_names):
# #     try:
#         menus_to_delete = self.env["ir.ui.menu"].search([
#             ("parent_id", "=", self.env.ref(
#                 "g2p_superset_dashboard.menu_superset_dashboard_embedded").id),
#             ("name", "in", dashboard_names)
#         ])
# #         if menus_to_delete:
#             menus_to_delete.unlink()
#             _logger.info(f"Menus for dashboards {dashboard_names} deleted successfully.")
#         else:
#             _logger.info(f"No menus found for dashboards {dashboard_names} to delete.")
#     except Exception as e:
#         _logger.error(f"Error while deleting menus: {e}")
#         raise

# # Regenerates all menus for the dashboards.
# # @api.model
# # def create_menus(self):
# #     try:
# #         # Clear all existing dynamic menus
#             existing_menus = self.env["ir.ui.menu"].search([
#                 ("parent_id", "=", self.env.ref(
#                     "g2p_superset_dashboard.menu_superset_dashboard_embedded").id)
#             ])
# #         existing_menus.unlink()

#         # Fetch all dashboards
#         dashboards = self.search([])

#         # Create or update menus for all dashboards
#         self._create_or_update_menus(dashboards)

#     except Exception as e:
#         _logger.error(f"Error while regenerating all menus: {e}")
#         raise
