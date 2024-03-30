from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRegistryConfig(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestRegistryConfig, cls).setUpClass()
        cls.config_model = cls.env["res.config.settings"]
        cls.ir_config_parameter_model = cls.env["ir.config_parameter"]

    def test_set_values(self):
        self.config_model.max_registrants_count_job_queue = 300
        self.config_model.batch_registrants_count_job_queue = 3000
        self.config_model.phone_regex = "^\\d{11}$"
        self.config_model.set_values()

        max_registrants_count = self.ir_config_parameter_model.sudo().get_param(
            "g2p_registry.max_registrants_count_job_queue"
        )
        batch_registrants_count = self.ir_config_parameter_model.sudo().get_param(
            "g2p_registry.batch_registrants_count_job_queue"
        )
        phone_regex = self.ir_config_parameter_model.sudo().get_param("g2p_registry.phone_regex")

        self.assertEqual(int(max_registrants_count), 300)
        self.assertEqual(int(batch_registrants_count), 3000)
        self.assertEqual(phone_regex, "^\\d{11}$")

    def test_get_values(self):
        self.ir_config_parameter_model.sudo().set_param("g2p_registry.max_registrants_count_job_queue", "400")
        self.ir_config_parameter_model.sudo().set_param(
            "g2p_registry.batch_registrants_count_job_queue", "3000"
        )
        self.ir_config_parameter_model.sudo().set_param("g2p_registry.phone_regex", "^\\d{11}$")
        config_values = self.config_model.get_values()

        self.assertEqual(int(config_values["max_registrants_count_job_queue"]), 400)

        self.assertEqual(int(config_values["batch_registrants_count_job_queue"]), 3000)

        self.assertEqual(config_values["phone_regex"], "^\\d{11}$")
