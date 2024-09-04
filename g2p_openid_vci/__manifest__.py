# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P OpenID VCI: Base",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "Other OSI approved licence",
    "depends": [
        "g2p_registry_base",
        "g2p_encryption",
    ],
    "external_dependencies": {"python": ["cryptography<37", "python-jose", "jq", "PyLD"]},
    "data": [
        "security/ir.model.access.csv",
        "views/vci_issuers.xml",
    ],
    "assets": {
        "web.assets_backend": [],
        "web.assets_qweb": [],
    },
    "demo": [],
    "images": [],
    "application": False,
    "installable": True,
    "auto_install": False,
}
