import json
import logging
from datetime import date, datetime

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MisConfig(models.Model):
    _name = "mis.config"
    _description = "MIS Configuration"

    name = fields.Char(required=True)
    mis_api_url = fields.Char(string="MIS API URL", required=True)
    mis_login_url = fields.Char(string="MIS Login URL", required=True)
    mis_logout_url = fields.Char(string="MIS Logout URL", required=True)
    database = fields.Char(required=True)
    username = fields.Char(required=True)
    password = fields.Char(required=True)
    last_updated_at = fields.Datetime()
    cron_id = fields.Many2one("ir.cron", string="Cron Job", required=False)
    job_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("running", "Running"),
            ("completed", "Completed"),
        ],
        string="Status",
        required=True,
        default="draft",
    )
    interval_minutes = fields.Integer(string="Interval in minutes", required=True, default=10)
    session_token = fields.Char()
    mis_id_type = fields.Many2one("g2p.id.type", string="MIS ID Type", required=True)
    mis_program_id = fields.Many2one("g2p.program", string="MIS Program ID", required=True)

    def login(self):
        url = self.mis_login_url
        payload = {
            "jsonrpc": "2.0",
            "params": {
                "db": self.database,
                "login": self.username,
                "password": self.password,
            },
        }
        response = requests.post(url, json=payload, timeout=10)
        try:
            response.raise_for_status()
            self.session_token = response.cookies.get("session_id")
        except Exception:
            _logger.error(f"Login failed with status code: {response.status_code}")
            raise

    def logout(self):
        url = self.mis_logout_url
        cookies = {"session_id": self.session_token}

        response = requests.get(url, cookies=cookies, timeout=10)

        try:
            response.raise_for_status()
            self.session_token = None
        except Exception:
            _logger.error(f"Logout failed with status code: {response.status_code}")

    def test_connection(self):
        self.ensure_one()
        self.login()

        try:
            test_url = self.mis_api_url
            response = requests.get(test_url, cookies={"session_id": self.session_token}, timeout=10)
            response.raise_for_status()

        except Exception as e:
            _logger.error(f"Test Connection failed: {str(e)}")
            raise UserError(_("Failed to connect to remote MIS")) from e
        finally:
            self.logout()

    # TODO: Split the methods into smaller methods
    # ruff: noqa: C901
    def import_records(self, config_id=None):
        if config_id:
            config = self.browse(config_id)
        else:
            config = self

        config.ensure_one()

        config.login()
        is_updated = False
        individuals_list = []

        import_url = config.mis_api_url

        response = requests.get(import_url, cookies={"session_id": config.session_token}, timeout=10)
        response.raise_for_status()
        response = response.json()

        for item in response:
            group = None
            create_date_str = item.get("create_date")
            create_date = datetime.strptime(create_date_str, "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)
            write_date_str = item.get("write_date")
            write_date = datetime.strptime(write_date_str, "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)
            prog_reg_info = item.get("program_membership_ids", None)
            if prog_reg_info:
                prog_reg_info = prog_reg_info[0].get("program_registrant_info_ids", None)
            if prog_reg_info:
                prog_reg_info = prog_reg_info[0].get("program_registrant_info", None)

            if (not config.last_updated_at) or create_date > config.last_updated_at:
                group = self.env["res.partner"].create(
                    {
                        "name": item.get("name"),
                        "is_group": item.get("is_group"),
                        "is_registrant": True,
                        "registration_date": item.get("registration_date"),
                        "reg_ids": [
                            (
                                0,
                                0,
                                {
                                    "id_type": self.env["g2p.id.type"]
                                    .search(
                                        [("name", "=", reg_id.get("id_type", None))],
                                    )[0]
                                    .id,
                                    "value": reg_id.get("value", None),
                                    "expiry_date": reg_id.get("expiry_date", None),
                                },
                            )
                            for reg_id in item.get("ids")
                        ]
                        + [
                            (
                                0,
                                0,
                                {
                                    "id_type": config.mis_id_type.id,
                                    "value": item.get("id"),
                                },
                            )
                        ],
                        "phone_number_ids": [
                            (
                                0,
                                0,
                                {
                                    "phone_no": phone.get("phone_no"),
                                    "date_collected": phone.get("date_collected"),
                                    "disabled": phone.get("disabled"),
                                },
                            )
                            for phone in item.get("phone_numbers")
                        ],
                        "email": item.get("email"),
                        "address": item.get("address"),
                        "bank_ids": [
                            (
                                0,
                                0,
                                {
                                    "bank_id": self.env["res.bank"]
                                    .search([("name", "=", bank.get("bank_name"))], limit=1)[0]
                                    .id,
                                    "acc_number": bank.get("acc_number"),
                                },
                            )
                            for bank in item.get("bank_ids")
                        ],
                        "program_membership_ids": [
                            (
                                0,
                                0,
                                {
                                    "program_id": config.mis_program_id.id,
                                    "state": "draft",
                                    "enrollment_date": date.today(),
                                },
                            )
                        ],
                        "program_registrant_info_ids": [
                            (
                                0,
                                0,
                                {
                                    "program_id": config.mis_program_id.id,
                                    "state": "active",
                                    "program_registrant_info": json.dumps(prog_reg_info)
                                    if prog_reg_info
                                    else None,
                                },
                            )
                        ],
                        "notification_preference": item.get("notification_preference", None),
                        "kind": self.env["g2p.group.kind"]
                        .search([("name", "=", item.get("kind", None))], limit=1)[0]
                        .id
                        if item.get("kind", None)
                        else None,
                        "is_partial_group": item.get("is_partial_group"),
                        "active": item.get("active"),
                    }
                )
                is_updated = True

            elif write_date > config.last_updated_at:
                group = (
                    self.env["g2p.reg.id"]
                    .search(
                        [
                            ("id_type", "=", config.mis_id_type.id),
                            ("value", "=", item.get("id")),
                            ("partner_id.is_group", "=", True),
                        ]
                    )[0]
                    .partner_id
                )
                group.update(
                    {
                        "name": item.get("name"),
                        "is_group": item.get("is_group"),
                        "registration_date": item.get("registration_date"),
                        "reg_ids": [
                            (5,),
                        ]
                        + [
                            (
                                0,
                                0,
                                {
                                    "id_type": self.env["g2p.id.type"]
                                    .search(
                                        [("name", "=", reg_id.get("id_type", None))],
                                    )[0]
                                    .id,
                                    "value": reg_id.get("value", None),
                                    "expiry_date": reg_id.get("expiry_date", None),
                                },
                            )
                            for reg_id in item.get("ids")
                        ]
                        + [
                            (
                                0,
                                0,
                                {
                                    "id_type": config.mis_id_type.id,
                                    "value": item.get("id"),
                                },
                            )
                        ],
                        "phone_number_ids": [
                            (5,),
                        ]
                        + [
                            (
                                0,
                                0,
                                {
                                    "phone_no": phone.get("phone_no"),
                                    "date_collected": phone.get("date_collected"),
                                    "disabled": phone.get("disabled"),
                                },
                            )
                            for phone in item.get("phone_numbers")
                        ],
                        "email": item.get("email"),
                        "address": item.get("address"),
                        "bank_ids": [
                            (5,),
                        ]
                        + [
                            (
                                0,
                                0,
                                {
                                    "bank_id": self.env["res.bank"]
                                    .search([("name", "=", bank.get("bank_name"))], limit=1)[0]
                                    .id,
                                    "acc_number": bank.get("acc_number"),
                                },
                            )
                            for bank in item.get("bank_ids")
                        ],
                        "notification_preference": item.get("notification_preference", None),
                        "kind": self.env["g2p.group.kind"]
                        .search([("name", "=", item.get("kind", None))], limit=1)[0]
                        .id
                        if item.get("kind", None)
                        else None,
                        "is_partial_group": item.get("is_partial_group"),
                        "active": item.get("active"),
                        "program_registrant_info_ids": [
                            (5,),
                        ]
                        + [
                            (
                                0,
                                0,
                                {
                                    "program_id": config.mis_program_id.id,
                                    "state": "active",
                                    "program_registrant_info": json.dumps(prog_reg_info)
                                    if prog_reg_info
                                    else None,
                                },
                            )
                        ],
                    }
                )
                is_updated = True

            for membership in item.get("members"):
                individual = membership.get("individual")
                if not any(ind.get("id") == individual.get("id") for ind in individuals_list):
                    individuals_list.append(individual)

        for member in individuals_list:
            create_date_str = member.get("create_date")
            create_date = datetime.strptime(create_date_str, "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)
            write_date_str = member.get("write_date")
            write_date = datetime.strptime(write_date_str, "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)
            if (not config.last_updated_at) or create_date > config.last_updated_at:
                individual = self.env["res.partner"].create(
                    {
                        "name": member.get("name"),
                        "is_group": member.get("is_group"),
                        "registration_date": member.get("registration_date"),
                        "phone_number_ids": [
                            (
                                0,
                                0,
                                {
                                    "phone_no": phone.get("phone_no"),
                                    "date_collected": phone.get("date_collected"),
                                    "disabled": phone.get("disabled"),
                                },
                            )
                            for phone in member.get("phone_numbers")
                        ],
                        "reg_ids": [
                            (
                                0,
                                0,
                                {
                                    "id_type": self.env["g2p.id.type"]
                                    .search(
                                        [("name", "=", reg_id.get("id_type", None))],
                                    )[0]
                                    .id,
                                    "value": reg_id.get("value", None),
                                    "expiry_date": reg_id.get("expiry_date", None),
                                },
                            )
                            for reg_id in member.get("ids")
                        ]
                        + [
                            (
                                0,
                                0,
                                {
                                    "id_type": config.mis_id_type.id,
                                    "value": member.get("id"),
                                },
                            )
                        ],
                        "email": member.get("email"),
                        "address": member.get("address"),
                        "bank_ids": [
                            (
                                0,
                                0,
                                {
                                    "bank_id": self.env["res.bank"]
                                    .search([("name", "=", bank.get("bank_name"))], limit=1)[0]
                                    .id,
                                    "acc_number": bank.get("acc_number"),
                                },
                            )
                            for bank in member.get("bank_ids")
                        ],
                        "notification_preference": member.get("notification_preference", None),
                        "given_name": member.get("given_name"),
                        "addl_name": member.get("addl_name"),
                        "family_name": member.get("family_name"),
                        "gender": member.get("gender"),
                        "birthdate": member.get("birthdate"),
                        "birth_place": member.get("birth_place"),
                    }
                )

                is_updated = True
            elif write_date > config.last_updated_at:
                individual = (
                    self.env["g2p.reg.id"]
                    .search(
                        [
                            ("id_type", "=", config.mis_id_type.id),
                            ("value", "=", member.get("id")),
                            ("partner_id.is_group", "=", False),
                        ]
                    )[0]
                    .partner_id
                )
                individual.update(
                    {
                        "name": member.get("name"),
                        "is_group": member.get("is_group"),
                        "registration_date": member.get("registration_date"),
                        "phone_number_ids": [
                            (5,),
                        ]
                        + [
                            (
                                0,
                                0,
                                {
                                    "phone_no": phone.get("phone_no"),
                                    "date_collected": phone.get("date_collected"),
                                    "disabled": phone.get("disabled"),
                                },
                            )
                            for phone in member.get("phone_numbers")
                        ],
                        "reg_ids": [
                            (5,),
                        ]
                        + [
                            (
                                0,
                                0,
                                {
                                    "id_type": self.env["g2p.id.type"]
                                    .search(
                                        [("name", "=", reg_id.get("id_type", None))],
                                    )[0]
                                    .id,
                                    "value": reg_id.get("value", None),
                                    "expiry_date": reg_id.get("expiry_date", None),
                                },
                            )
                            for reg_id in member.get("ids")
                        ]
                        + [
                            (
                                0,
                                0,
                                {
                                    "id_type": config.mis_id_type.id,
                                    "value": member.get("id"),
                                },
                            )
                        ],
                        "email": member.get("email"),
                        "address": member.get("address"),
                        "bank_ids": [
                            (5,),
                        ]
                        + [
                            (
                                0,
                                0,
                                {
                                    "bank_id": self.env["res.bank"]
                                    .search([("name", "=", bank.get("bank_name"))], limit=1)[0]
                                    .id,
                                    "acc_number": bank.get("acc_number"),
                                },
                            )
                            for bank in member.get("bank_ids")
                        ],
                        "notification_preference": member.get("notification_preference", None),
                        "given_name": member.get("given_name"),
                        "addl_name": member.get("addl_name"),
                        "family_name": member.get("family_name"),
                        "gender": member.get("gender"),
                        "birthdate": member.get("birthdate"),
                        "birth_place": member.get("birth_place"),
                    }
                )
                is_updated = True
        for item in response:
            group = (
                self.env["g2p.reg.id"]
                .search(
                    [
                        ("id_type", "=", config.mis_id_type.id),
                        ("value", "=", item.get("id")),
                        ("partner_id.is_group", "=", True),
                    ]
                )[0]
                .partner_id
            )

            for membership in item.get("members"):
                member = membership.get("individual")
                individual = (
                    self.env["g2p.reg.id"]
                    .search(
                        [
                            ("id_type", "=", config.mis_id_type.id),
                            ("value", "=", member.get("id")),
                            ("partner_id.is_group", "=", False),
                        ]
                    )[0]
                    .partner_id
                )

                create_date_str = membership.get("create_date")
                create_date = datetime.strptime(create_date_str, "%Y-%m-%dT%H:%M:%S.%f%z").replace(
                    tzinfo=None
                )
                write_date_str = membership.get("write_date")
                write_date = datetime.strptime(write_date_str, "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)

                if (not config.last_updated_at) or create_date > config.last_updated_at:
                    group.update(
                        {
                            "group_membership_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "individual": individual.id,
                                        "kind": [
                                            (
                                                4,
                                                config.get_or_create_kind(member_kind.get("name")).id,
                                            )
                                            for member_kind in membership.get("kind")
                                        ],
                                    },
                                )
                            ]
                        }
                    )
                    is_updated = True
                elif write_date > config.last_updated_at:
                    group_membership = group.group_membership_ids.filter(individual=individual.id)
                    group_membership.update(
                        {
                            "kind": [
                                (5,),
                            ]
                            + [
                                (
                                    4,
                                    config.get_or_create_kind(member_kind.get("name")).id,
                                )
                                for member_kind in membership.get("kind")
                            ]
                        }
                    )
                    is_updated = True

        if is_updated:
            config.last_updated_at = datetime.utcnow()
        config.logout()

    def get_or_create_kind(self, kind_str):
        kind = self.env["g2p.group.membership.kind"].search([("name", "=", kind_str)], limit=1)
        if kind:
            kind = kind[0]
        else:
            kind = self.env["g2p.group.membership.kind"].sudo().create({"name": kind_str})

        return kind

    def mis_import_action_trigger(self):
        for rec in self:
            if rec.job_status == "draft" or rec.job_status == "completed":
                ir_cron = self.env["ir.cron"].sudo()
                rec.cron_id = ir_cron.create(
                    {
                        "name": "MIS Pull Cron " + rec.name + " #" + str(rec.id),
                        "active": True,
                        "interval_number": rec.interval_minutes,
                        "interval_type": "minutes",
                        "model_id": self.env["ir.model"].search([("model", "=", "mis.config")])[0].id,
                        "state": "code",
                        "code": "model.import_records(" + str(rec.id) + ")",
                        "doall": False,
                        "numbercall": -1,
                    }
                )
                _logger.info("Job Started")
                rec.job_status = "running"

            elif rec.job_status == "running":
                _logger.info("Job Stopped")
                rec.job_status = "completed"
                rec.sudo().cron_id.unlink()
                rec.cron_id = None
