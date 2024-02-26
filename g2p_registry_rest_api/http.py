import json

from werkzeug.exceptions import BadRequest, HTTPException, InternalServerError

import odoo
from odoo.http import Root
from odoo.tools.config import config

from odoo.addons.base_rest.core import _rest_services_routes
from odoo.addons.base_rest.http import HttpRestRequest, JSONEncoder, wrapJsonException

from .exceptions.base_exception import G2PApiException, G2PApiValidationError
from .models.error_response import G2PErrorResponse


def g2pFixException(exception, original_exception=None):
    get_original_headers = HTTPException(exception).get_headers

    def get_body(environ=None, scope=None):
        if original_exception and isinstance(original_exception, G2PApiException):
            res = G2PErrorResponse(
                errorCode=original_exception.error_code,
                errorMessage=original_exception.error_message,
                errorDescription=original_exception.error_description or "",
            ).dict()
        else:
            extra_info = getattr(exception, "rest_json_info", None)
            extra_info = json.dumps(extra_info) if extra_info else ""
            res = G2PErrorResponse(
                errorCode=exception.code,
                errorMessage=exception.get_description(environ),
                errorDescription=extra_info,
            ).dict()
        if config.get_misc("base_rest", "dev_mode"):
            # return exception info only if base_rest is in dev_mode
            res.update({"traceback": exception.traceback})
        return JSONEncoder().encode(res)

    def get_headers(environ=None, scope=None):
        """Get a list of headers."""
        _headers = [("Content-Type", "application/json")]
        for key, value in get_original_headers(environ=environ, scope=scope):
            if key != "Content-Type":
                _headers.append(key, value)
        return _headers

    exception.get_headers = get_headers
    exception.get_body = get_body
    return exception


class G2PHttpRestRequest(HttpRestRequest):
    def _handle_exception(self, exception):
        res = super()._handle_exception(exception)
        if isinstance(exception, G2PApiValidationError):
            res = wrapJsonException(BadRequest(exception.args[0]))
        elif isinstance(exception, G2PApiException):
            res = wrapJsonException(InternalServerError(exception.args[0]))
        g2pFixException(res, exception)
        return res


ori_get_request = Root.get_request


def get_request(self, httprequest):
    db = httprequest.session.db
    if db and odoo.service.db.exp_db_exist(db):
        odoo.registry(db)
        rest_routes = _rest_services_routes.get(db, [])
        for root_path in rest_routes:
            if httprequest.path.startswith(root_path):
                return G2PHttpRestRequest(httprequest)
    return ori_get_request(self, httprequest)


Root.get_request = get_request
