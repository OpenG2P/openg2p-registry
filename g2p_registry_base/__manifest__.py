# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Registry: Base",
    "category": "G2P",
    "version": "17.0.1.3.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["base", "mail", "contacts", "web", "portal"],
    "data": [
        "data/ir_config_params.xml",
        "security/g2p_security.xml",
        "security/ir.model.access.csv",
        "wizard/disable_registrant_view.xml",
        "views/main_view.xml",
        "views/reg_relationship_view.xml",
        "views/relationships_view.xml",
        "views/reg_id_view.xml",
        "views/id_types_view.xml",
        "views/phone_number_view.xml",
        "views/tags_view.xml",
        "views/res_config_view.xml",
        "views/district_config.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/g2p_registry_base/static/src/xml/custom_web.xml",
        ],
    },
    "application": False,
    "installable": True,
    "auto_install": False,
}
