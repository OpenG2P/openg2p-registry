# Part of OpenG2P Social Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Registry Deduplication - Deduplicator",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "g2p_registry_individual",
    ],
    "external_dependencies": {},
    "data": [
        "security/ir.model.access.csv",
        "data/default_deduplicator_config.xml",
        "views/deduplicator_config_view.xml",
        "views/individual_view.xml",
        "views/res_config_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "g2p_registry_deduplication_deduplicator/static/src/js/view_duplicates.js",
            "g2p_registry_deduplication_deduplicator/static/src/xml/view_duplicates_template.xml",
        ],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
