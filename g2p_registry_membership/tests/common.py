# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

from odoo.tests import common

# from odoo.addons.queue_job.job import Job


class JobCommonCase(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                test_queue_job_no_delay=True,
            )
        )
