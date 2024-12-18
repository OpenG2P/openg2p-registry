# Part of openG2P. See LICENSE file for full copyright and licensing details.

{
    "name": "G2P ODK Importer",
    "category": "Connector",
    "summary": "Import records from ODK",
    "version": "17.0.1.4.0",
    "sequence": 3,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "base",
        "queue_job",
        "g2p_documents",
        "g2p_registry_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/odk_config_views.xml",
        "views/odk_import_views.xml",
        "views/odk_menu.xml",
        "views/res_config_view.xml",
    ],
    "external_dependencies": {
        "python": [
            "jq",
        ]
    },
    "application": True,
    "installable": True,
    "auto_install": False,
}
