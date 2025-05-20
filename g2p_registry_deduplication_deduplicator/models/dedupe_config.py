import logging
import os

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class G2PDedupeConfigField(models.Model):
    _name = "g2p.registry.deduplication.deduplicator.config.field"
    _description = "Deduplicator Config Field"

    name = fields.Char(required=True)
    fuzziness = fields.Char()
    weightage = fields.Float()
    exact = fields.Boolean()

    dedupe_config_id = fields.Many2one(
        "g2p.registry.deduplication.deduplicator.config", ondelete="cascade", required=True
    )


class G2PDedupeConfig(models.Model):
    _name = "g2p.registry.deduplication.deduplicator.config"
    _description = "Deduplicator Config"

    name = fields.Char(required=True)

    config_name = fields.Char(required=True, default="default")

    dedupe_service_base_url = fields.Char(
        default=os.getenv(
            "DEDUPLICATOR_SERVICE_BASE_URL", "http://socialregistry-deduplicator-openg2p-deduplicator"
        )
    )
    dedupe_service_api_timeout = fields.Integer(default=10)

    config_index_name = fields.Char(default="res_partner")
    config_fields = fields.One2many(
        "g2p.registry.deduplication.deduplicator.config.field", "dedupe_config_id"
    )
    config_score_threshold = fields.Float()

    active = fields.Boolean(required=True)

    _sql_constraints = [
        ("unique_config_name", "unique (config_name)", "Dedupe Config with same config name already exists !")
    ]

    def save_upload_config(self):
        for rec in self:
            res = requests.put(
                f"{rec.dedupe_service_base_url.rstrip('/')}/config/{rec.config_name}",
                timeout=rec.dedupe_service_api_timeout,
                json={
                    "index": rec.config_index_name,
                    "fields": [
                        {
                            "name": rec_field.name,
                            "fuzziness": rec_field.fuzziness,
                            "boost": rec_field.weightage,
                            **({"query_type": "term"} if rec_field.exact else {}),
                        }
                        for rec_field in rec.config_fields
                    ],
                    "score_threshold": rec.config_score_threshold,
                    "active": rec.active,
                },
            )
            try:
                res.raise_for_status()
            except Exception as e:
                _logger.exception("Error uploading config")
                raise ValidationError(_("Error uploading config")) from e

    @api.model
    def get_configured_deduplicator(self):
        dedupe_config_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("g2p_registry_deduplication_deduplicator.deduplicator_config_id", None)
        )
        return self.browse(int(dedupe_config_id)) if dedupe_config_id else None

    @api.model
    def get_duplicates_by_record_id(self, record_id, config_id=None):
        if config_id:
            dedupe_config = self.browse(config_id)
        else:
            dedupe_config = self.get_configured_deduplicator()
        res = requests.get(
            f"{dedupe_config.dedupe_service_base_url.rstrip('/')}/getDuplicates/{record_id}",
            timeout=dedupe_config.dedupe_service_api_timeout,
        )
        try:
            res.raise_for_status()
        except Exception as e:
            raise ValidationError(_("Error retrieving duplicates")) from e
        duplicates = res.json().get("duplicates")
        for entry in duplicates:
            duplicate_record = self.env["res.partner"].sudo().browse(entry.get("id"))
            entry["name"] = duplicate_record.name
        return duplicates
