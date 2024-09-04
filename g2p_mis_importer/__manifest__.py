# Part of openG2P. See LICENSE file for full copyright and licensing details.

{
    "name": "G2P MIS Importer",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["g2p_programs", "queue_job"],
    "data": [
        "security/ir.model.access.csv",
        "views/mis_config_views.xml",
        "views/mis_menu.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
}
