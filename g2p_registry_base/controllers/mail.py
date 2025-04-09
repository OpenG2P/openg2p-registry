import logging

from markupsafe import Markup
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import consteq
from odoo.tools.translate import _

from odoo.addons.mail.controllers.attachment import AttachmentController
from odoo.addons.mail.controllers.thread import ThreadController
from odoo.addons.mail.models.discuss.mail_guest import add_guest_to_context

logger = logging.getLogger(__name__)


class G2PAttachmentController(AttachmentController):
    @http.route("/mail/attachment/delete", methods=["POST"], type="json", auth="public")
    @add_guest_to_context
    def mail_attachment_delete(self, attachment_id, access_token=None):
        attachment = request.env["ir.attachment"].browse(int(attachment_id)).exists()
        if not attachment:
            target = request.env.user.partner_id
            request.env["bus.bus"]._sendone(target, "ir.attachment/delete", {"id": attachment_id})
            return
        message = request.env["mail.message"].search([("attachment_ids", "in", attachment.ids)], limit=1)
        # Check if current user is admin or the creator (user or guest)
        is_admin = request.env.user.has_group("base.group_system")
        is_author = message.is_current_user_or_guest_author
        if not (is_admin or is_author):
            raise AccessError(_("You do not have permission to delete this attachment."))

        if not request.env.user.share:
            # Check through standard access rights/rules for internal users.
            attachment._delete_and_notify(message)
            return

        # Portal/Guest users handling
        attachment_sudo = attachment.sudo()
        if message:
            # Only the message's author can delete linked attachments
            if not message.is_current_user_or_guest_author:
                raise NotFound()
        else:
            # Access token is required for guests or portal users to delete attachments
            if (
                not access_token
                or not attachment_sudo.access_token
                or not consteq(access_token, attachment_sudo.access_token)
            ):
                raise NotFound()
            if attachment_sudo.res_model != "mail.compose.message" or attachment_sudo.res_id != 0:
                raise NotFound()
        attachment_sudo._delete_and_notify(message)


class G2PThreadController(ThreadController):
    @http.route("/mail/message/update_content", methods=["POST"], type="json", auth="public")
    @add_guest_to_context
    def mail_message_update_content(
        self, message_id, body, attachment_ids, attachment_tokens=None, partner_ids=None
    ):
        guest = request.env["mail.guest"]._get_guest_from_context()
        guest.env["ir.attachment"].browse(attachment_ids)._check_attachments_access(attachment_tokens)
        message_sudo = guest.env["mail.message"].browse(message_id).sudo().exists()

        # Check if current user is admin or the creator (user or guest)
        is_admin = request.env.user.has_group("base.group_system")
        is_author = message_sudo.is_current_user_or_guest_author
        if not (is_admin or is_author):
            raise AccessError(_("You do not have permission to update this message."))

        if not message_sudo.model or not message_sudo.res_id:
            raise NotFound()
        body = Markup(body) if body else body  # may contain HTML such as @mentions
        guest.env[message_sudo.model].browse([message_sudo.res_id])._message_update_content(
            message_sudo, body, attachment_ids=attachment_ids, partner_ids=partner_ids
        )
        return message_sudo.message_format()[0]
