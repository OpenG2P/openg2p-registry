# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Auth: OIDC - Reg ID",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["g2p_auth_oidc", "g2p_registry_individual", "g2p_registry_group"],
    "data": [
        "views/g2p_auth_id_oidc_provider.xml",
        "views/g2p_id_type.xml",
        "views/individual.xml",
        "views/group.xml",
        "views/templates.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "g2p_auth_id_oidc/static/src/js/authentication_status.js",
            "g2p_auth_id_oidc/static/src/xml/authentication_status.xml",
        ],
        "web.assets_qweb": [],
    },
    "demo": [],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": False,
}
