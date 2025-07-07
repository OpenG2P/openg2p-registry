# Part of OpenG2P. See LICENSE file for full copyright and licensing details.

{
    "name": "G2P Security",
    "category": "G2P",
    "version": "17.0.1.5.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["g2p_registry_base", "auth_signup", "password_security"],
    "data": [
        "data/ir_config_parameter_data.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/res_partner_change_pass.xml",
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
}
