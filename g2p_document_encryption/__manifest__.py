# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Documents Encryption",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["g2p_documents", "g2p_encryption"],
    "data": [
        "views/document_store.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "g2p_document_encryption/static/src/xml/preview_document.xml",
            "g2p_document_encryption/static/src/js/preview_document.js",
        ],
    },
    "demo": [],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": False,
}
