{
    "name": "G2P Encryption: Keymanager",
    "category": "G2P",
    "version": "17.0.1.3.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": [
        "g2p_encryption",
    ],
    "external_dependencies": {"python": ["cryptography>36,<37", "jwcrypto", "python-jose"]},
    "data": [
        "views/encryption_provider.xml",
        "data/default_provider.xml",
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
