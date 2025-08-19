# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

{
    "name": "G2P ODK Importer",
    "category": "G2P",
    "summary": "Import records from ODK",
    "version": "17.0.0.0.0",
    "sequence": 3,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "base",
        "queue_job",
        "g2p_registry_base",
        "g2p_enumerator",
    ],
    "data": [
        "security/odk_groups.xml",
        "security/ir.model.access.csv",
        "views/odk_config_views.xml",
        "views/odk_import_views.xml",
        "views/odk_menu.xml",
    ],
    "external_dependencies": {
        "python": [
            "jq",
        ]
    },
    "application": False,
    "installable": True,
    "auto_install": False,
}
