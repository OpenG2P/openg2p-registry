import json

from psycopg2.extras import Json

from odoo import fields


class JSONField(fields.Field):

    type = "json"
    column_type = ("json", "json")

    def convert_to_column(self, value, record, values=None, validate=True):
        if value is None:
            return None
        else:
            return Json(value, dumps=lambda x: json.dumps(x, separators=(",", ":")))
