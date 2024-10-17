# Part of OpenG2P. See LICENSE file for full copyright and licensing details.
{
    "name": "G2P Portal Auth",
    "category": "G2P",
    "version": "17.0.1.4.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["g2p_auth_oidc"],
    "data": [
        "views/auth_oauth_provider.xml",
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
