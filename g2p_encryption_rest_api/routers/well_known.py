import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from odoo.api import Environment

from odoo.addons.fastapi.dependencies import odoo_env

_logger = logging.getLogger(__name__)

well_known_router = APIRouter(prefix="/.well-known", tags=["well-known"])


@well_known_router.get("/jwks.json")
def get_jwks(
    env: Annotated[Environment, Depends(odoo_env)],
):
    encryption_providers = env["g2p.encryption.provider"].sudo().search([])
    jwks = []
    for prov in encryption_providers:
        try:
            prov_jwks = prov.get_jwks()
            jwks.extend(prov_jwks.get("keys", []) if prov_jwks else [])
        except Exception:
            _logger.exception("Unable to get JWKS from list of encryption providers")
    return {"keys": jwks}
