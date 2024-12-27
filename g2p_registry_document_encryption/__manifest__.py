# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Registry: Documents Encryption",
    "category": "G2P",
    "version": "17.0.1.4.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["g2p_registry_documents", "g2p_registry_encryption", "g2p_documents"],
    "data": [
        "views/registrant_document_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "g2p_registry_document_encryption/static/src/js/preview_document.js",
        ],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
