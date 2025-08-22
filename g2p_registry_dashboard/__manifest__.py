# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "OpenG2P Registry: Dashboard",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["g2p_registry"],
    "external_dependencies": {},
    "data": ["data/cron_job.xml", "views/menu.xml"],
    "assets": {
        "web.assets_backend": [
            "g2p_registry_dashboard/static/src/components/chart/**/*",
            "g2p_registry_dashboard/static/src/components/kpi/**/*",
            "g2p_registry_dashboard/static/src/js/dashboard.js",
            "g2p_registry_dashboard/static/src/xml/dashboard.xml",
        ],
    },
    "demo": [],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": True,
    "post_init_hook": "init_materialized_view",
    "uninstall_hook": "drop_materialized_view",
}
