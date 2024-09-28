# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Superset Dashboard",
    "category": "G2P",
    "version": "17.0.1.3.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["base", "web"],
    "external_dependencies": {},
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/superset_dashboard_config_views.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "assets": {
        "web.assets_backend": [
            "g2p_superset_dashboard/static/src/components/**/*.js",
            "g2p_superset_dashboard/static/src/components/**/*.xml",
            "g2p_superset_dashboard/static/src/components/**/*.css",
            "g2p_superset_dashboard/static/src/components/**/*.scss",
        ],
    },
    "uninstall_hook": "uninstall_hook",
}
