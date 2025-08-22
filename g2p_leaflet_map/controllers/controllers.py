import json

from odoo import http
from odoo.http import request


class OSMConfigController(http.Controller):
    @http.route("/osm/config/get", type="http", auth="public", methods=["GET"], cors="*")
    def get_osm_config(self):
        config = request.env["g2p.osm.config"].sudo().search([], limit=1)
        return request.make_response(
            json.dumps(
                {
                    "tile_server_url": config.tile_server_url,
                }
            ),
            headers=[("Content-Type", "application/json")],
        )
