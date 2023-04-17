# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Registry Documents",
    "category": "G2P",
    "version": "15.0.1.1.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "development_status": "Alpha",
    "depends": [
        "g2p_registry_base",
        "storage_backend_s3",
        "storage_file",
    ],
    "data": [
        "views/g2p_document_store.xml",
        "views/g2p_document_files.xml",
        # "security/ir.model.access.csv",
    ],
    "external_dependencies": {
        "python": ["Wkhtmltopdf", "boto3<=1.15.18", "python_slugify"]
    },
    "assets": {},
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
