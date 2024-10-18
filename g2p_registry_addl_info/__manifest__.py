{
    "name": "G2P Registry: Additional Info",
    "category": "G2P",
    "version": "17.0.1.4.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "g2p_registry_base",
        "g2p_registry_individual",
        "g2p_registry_group",
    ],
    "data": [
        "views/registrant_individual.xml",
        "views/registrant_group.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "/g2p_registry_addl_info/static/src/js/g2p_additional_info.js",
            "/g2p_registry_addl_info/static/src/xml/g2p_additional_info.xml",
        ],
    },
    "demo": [],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": False,
}
