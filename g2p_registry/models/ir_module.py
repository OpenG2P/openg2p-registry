import logging

from odoo import models

_logger = logging.getLogger(__name__)


class IrModule(models.Model):
    _inherit = "ir.module.module"

    def _hide_unwanted_menus(self):
        menu_ids = [
            "account.menu_finance",
            "mass_mailing.mass_mailing_menu_root",
            "utm.menu_link_tracker_root",
            "survey.menu_surveys",
            "project.menu_main_pm",
            "project_todo.menu_todo_todos",
            "calendar.mail_menu_calendar",
            "event.event_main_menu",
            "hr.menu_hr_root",
            "contacts.menu_contacts",
            "mail.menu_root_discuss",
            "gamification.gamification_menu",
            "base.menu_translation",
        ]

        for xml_id in menu_ids:
            try:
                menu = self.env.ref(xml_id, raise_if_not_found=False)
                if menu:
                    menu.write({"active": False})
            except Exception as e:
                _logger.warning(f"[FAILED MENU HIDE] {xml_id} - {str(e)}")

    def write(self, vals):
        result = super().write(vals)

        if vals.get("state") in ["installed", "to upgrade"]:
            self._hide_unwanted_menus()

        return result
