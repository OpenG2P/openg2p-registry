from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestResConfigSettings(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_model = cls.env["res.config.settings"]
        cls.id_type_model = cls.env["g2p.id.type"]

        # Setup ID types for testing
        cls.vid_type = cls.id_type_model.create({"name": "Test VID Type"})
        cls.uin_type = cls.id_type_model.create({"name": "Test UIN Type"})

    def test_config_settings(self):
        """Test configuration settings fields and constraints"""
        config = self.config_model.create(
            {
                "g2p_mts_vid_delete_job_status": True,
                "g2p_mts_vid_delete_search_domain": "[('state', '=', 'draft')]",
                "g2p_mts_vid_id_type": self.vid_type.id,
                "g2p_mts_uin_token_id_type": self.uin_type.id,
            }
        )

        config._constrains_vehicle()
        job_cron = self.env.ref("g2p_mts.to_delete_g2p_reg_id_vid")
        self.assertTrue(job_cron.active, "Job cron should be active when status is True")

        self.assertEqual(
            config.g2p_mts_vid_delete_search_domain,
            "[('state', '=', 'draft')]",
            "Search domain not saved correctly",
        )
        self.assertEqual(config.g2p_mts_vid_id_type.id, self.vid_type.id, "VID type not saved correctly")
        self.assertEqual(
            config.g2p_mts_uin_token_id_type.id, self.uin_type.id, "UIN token type not saved correctly"
        )
