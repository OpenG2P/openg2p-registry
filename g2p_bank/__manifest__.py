# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Registry: Bank Details",
    "category": "G2P",
    "version": "15.0.1.1.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "development_status": "Production/Stable",
    "depends": [
        "base",
        "mail",
        "contacts",
        "g2p_registry_group",
        "g2p_registry_individual",
    ],
    "external_dependencies": {"python": ["schwifty"]},
    "data": [
        "views/individuals_view.xml",
        "views/groups_view.xml",
    ],
    "assets": {},
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
