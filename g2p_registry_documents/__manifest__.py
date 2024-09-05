# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Registry: Documents",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "g2p_documents",
        "g2p_registry_base",
        "g2p_registry_individual",
        "g2p_registry_group",
    ],
    "data": [
        "views/registrant_document_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "g2p_registry_documents/static/src/js/preview_document.js",
        ],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
