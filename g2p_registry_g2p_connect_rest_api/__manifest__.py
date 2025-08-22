# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P: G2P Connect REST API",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "g2p_registry_membership",
        "fastapi",
        "graphql_base",
    ],
    "data": [
        "data/ir_config_params.xml",
        "data/fastapi_endpoint_g2p_connect.xml",
    ],
    "external_dependencies": {"python": ["python-jose"]},
    "application": False,
    "auto_install": False,
    "installable": True,
}
