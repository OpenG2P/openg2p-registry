{
    "name": "G2P Registry: Additional Info",
    "category": "G2P",
    "version": "15.0.1.1.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://github.com/openg2p/openg2p-registry",
    "license": "Other OSI approved licence",
    "development_status": "Alpha",
    "depends": [
        "g2p_json_field",
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
        ],
        "web.assets_qweb": [
            "/g2p_registry_addl_info/static/src/xml/g2p_additional_info.xml",
        ],
    },
    "demo": [],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": False,
}
