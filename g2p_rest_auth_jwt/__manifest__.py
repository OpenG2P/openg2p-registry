# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P JWT Rest API Authentication",
    "category": "G2P",
    "version": "15.0.0.0.1",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://github.com/openg2p/openg2p-registry",
    "license": "Other OSI approved licence",
    "development_status": "Alpha",
    "maintainers": ["jeremi", "gonzalesedwin1123"],
    "depends": ["base_rest"],
    "external_dependencies": {
        "python": [
            "apispec",
            "jwt>=2.4.0",
            "pyOpenSSL==22.0.0",
        ]
    },
    "data": [
        "security/ir.model.access.csv",
        "views/auth_jwt_validator_views.xml",
    ],
    "assets": {},
    "demo": [],
    "images": [],
    "application": True,
    "installable": True,
    "auto_install": False,
}
