[
    {
        "id": .credential_type,
        "format": .supported_format,
        "scope": .scope,
        "cryptographic_binding_methods_supported": [
            "did:jwk"
        ],
        "credential_signing_alg_values_supported": [
            "RS256"
        ],
        "proof_types_supported": [
            "jwt"
        ],
        "credential_definition": {
            "type": [
                "VerifiableCredential",
                .credential_type
            ],
            "credentialSubject": {
                "fullName": {
                    "display": [
                        {
                            "name": "Household Name",
                            "locale": "en"
                        }
                    ]
                },
                "addressLine1": {
                    "display": [
                        {
                            "name": "Household Address Line 1",
                            "locale": "en"
                        }
                    ]
                },
                "locality": {
                    "display": [
                        {
                            "name": "Household Locality",
                            "locale": "en"
                        }
                    ]
                },
                "region": {
                    "display": [
                        {
                            "name": "Household Region",
                            "locale": "en"
                        }
                    ]
                },
                "UIN": {
                    "display": [
                        {
                            "name": "Household ID",
                            "locale": "en"
                        }
                    ]
                },
                "headName": {
                    "display": [
                        {
                            "name": "Household Head Name",
                            "locale": "en"
                        }
                    ]
                },
                "headGender": {
                    "display": [
                        {
                            "name": "Household Head Gender",
                            "locale": "en"
                        }
                    ]
                },
                "headDateOfBirth": {
                    "display": [
                        {
                            "name": "Household Head Date of Birth",
                            "locale": "en"
                        }
                    ]
                },
                "headNationalID": {
                    "display": [
                        {
                            "name": "Household Head National ID",
                            "locale": "en"
                        }
                    ]
                },
                "members": {
                    "display": [
                        {
                            "name": "Other Household Members",
                            "locale": "en"
                        }
                    ]
                }
            }
        },
        "display": [
            {
                "name": .name,
                "locale": "en",
                "logo": {
                    "url": (.web_base_url + "/g2p_openid_vci_group/static/description/icon.png"),
                    "alt_text": "a square logo of a OpenG2P"
                },
                "background_color": "#d1a1bd",
                "text_color": "#2e100a"
            }
        ],
        "order": [
            "fullName",
            "UIN",
            "addressLine1",
            "locality",
            "region",
            "headName",
            "headGender",
            "headDateOfBirth",
            "members"
        ]
    }
]
