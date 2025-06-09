# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Registry: Rest API",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "g2p_registry_membership",
        "fastapi",
        "extendable_fastapi",
    ],
    "external_dependencies": {"python": ["extendable-pydantic", "pydantic"]},
    "data": [
        "data/fastapi_endpoint_registry.xml",
        "security/g2p_security.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {},
    "demo": [],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": False,
}
