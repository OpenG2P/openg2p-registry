from odoo import api, fields, models


class DraftGroupAddMembersWizard(models.TransientModel):
    _name = "draft.group.add.members.wizard"
    _description = "Add Group Members Wizard"

    group_id = fields.Many2one(
        "draft.record", string="Group", required=True, domain=[("is_group", "=", True)]
    )
    line_ids = fields.One2many("draft.group.membership.wizard.line", "wizard_id", string="Group Members")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        group_id = self._context.get("default_group_id")
        if group_id:
            group = self.env["draft.record"].browse(group_id)
            res["group_id"] = group_id
            if group and group.group_member_ids_json:
                member_ids = group.group_member_ids_json
                members = self.env["draft.record"].browse(member_ids)

                unique_member_ids = set()
                lines = []
                for member in members:
                    if member.id not in unique_member_ids:
                        unique_member_ids.add(member.id)
                        lines.append((0, 0, {"member_id": member.id}))
                res["line_ids"] = lines
        return res

    def action_save_members(self):
        self.ensure_one()
        self.group_id.group_member_ids_json = [line.member_id.id for line in self.line_ids]
        return {"type": "ir.actions.act_window_close"}


class DraftGroupMembershipWizardLine(models.TransientModel):
    _name = "draft.group.membership.wizard.line"
    _description = "Draft Group Membership Wizard Line"

    wizard_id = fields.Many2one("draft.group.add.members.wizard", required=True, ondelete="cascade")
    member_id = fields.Many2one(
        "draft.record", string="Member", required=True, domain=[("is_group", "=", False)]
    )

    name = fields.Char(related="member_id.name", readonly=True)
    gender = fields.Char(related="member_id.gender", readonly=True)
    phone = fields.Char(related="member_id.phone", readonly=True)
    region = fields.Char(related="member_id.region", readonly=True)
