# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Draft Publish",
    "category": "G2P",
    "version": "17.0.1.6.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["base", "mail", "g2p_registry_membership", "g2p_registry_addl_info", "web"],
    "data": [
        "security/rules.xml",
        "security/ir.model.access.csv",
        "wizards/group_member.xml",
        "views/draft_records.xml",
        "wizards/rejection.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "g2p_draft_publish/static/src/**/*.js",
            "g2p_draft_publish/static/src/**/*.css",
            "g2p_draft_publish/static/src/**/*.scss",
            "g2p_draft_publish/static/src/**/*.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": True,
}
