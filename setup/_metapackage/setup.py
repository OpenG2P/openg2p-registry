import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-openg2p-openg2p-registry",
    description="Meta package for openg2p-openg2p-registry Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-g2p_bank>=15.0dev,<15.1dev',
        'odoo-addon-g2p_registry_base>=15.0dev,<15.1dev',
        'odoo-addon-g2p_registry_group>=15.0dev,<15.1dev',
        'odoo-addon-g2p_registry_individual>=15.0dev,<15.1dev',
        'odoo-addon-g2p_registry_membership>=15.0dev,<15.1dev',
        'odoo-addon-g2p_registry_rest_api>=15.0dev,<15.1dev',
        'odoo-addon-g2p_registry_rest_api_extension_demo>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
