# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Registry: Membership",
    "category": "G2P",
    "version": "15.0.0.0.1",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org/",
    "license": "Other OSI approved licence",
    "depends": [
        "base",
        "mail",
        "contacts",
        "g2p_registry_group",
        "g2p_registry_individual",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/group_membership_kinds.xml",
        "views/groups_view.xml",
        "views/individuals_view.xml",
        "views/group_membership_view.xml",
        "views/group_membership_kinds_view.xml",
    ],
    "assets": {},
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
