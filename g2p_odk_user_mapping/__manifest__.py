{
    "name": "ODK App User Mapping",
    "category": "G2P",
    "version": "17.0.0.0.0",
    "sequence": 1,
    "author": "OpenG2P",
    "website": "https://openg2p.org",
    "license": "LGPL-3",
    "depends": ["base", "account", "g2p_odk_importer"],
    "data": [
        "security/ir.model.access.csv",
        "views/registration_user_backend_view.xml",
        "views/odk_app_user.xml",
    ],
    "assets": {
        "web.assets_frontend": [],
        "web.assets_common": [],
        "website.assets_wysiwyg": [],
        "web.assets_backend": [
            "g2p_odk_user_mapping/static/src/css/style.css",
        ],
    },
    "application": False,
    "installable": True,
    "auto_install": True,
}
