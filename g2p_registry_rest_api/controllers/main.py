from odoo.addons.base_rest.controllers import main


class RegistryApiController(main.RestController):
    _root_path = "/api/v1/registry/"
    _collection_name = "base.rest.registry.services"
    _default_auth = "user"
