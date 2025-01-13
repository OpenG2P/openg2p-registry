# Part of OpenG2P Documents. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Documents Store",
    "category": "G2P",
    "version": "17.0.1.4.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["storage_backend_s3", "storage_file", "web"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/main_view.xml",
        "views/g2p_document_store.xml",
        "views/g2p_document_files.xml",
        "views/g2p_document_tags.xml",
        "data/storage_backend.xml",
    ],
    "external_dependencies": {"python": ["boto3<=1.15.18", "python_slugify"]},
    "assets": {
        "web.assets_backend": [
            "g2p_documents/static/src/js/preview_document.js",
        ],
    },
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
