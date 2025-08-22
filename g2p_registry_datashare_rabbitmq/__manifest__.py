# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Registry Datashare: RabbitMQ",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["queue_job", "g2p_registry_base", "g2p_registry_individual", "g2p_registry_group"],
    "external_dependencies": {"python": ["jq", "pika"]},
    "data": [
        "views/datashare_config_rabbitmq.xml",
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [],
    },
    "demo": [],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": True,
}
