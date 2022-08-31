# Part of OpenG2P Registry. See LICENSE file for full copyright and licensing details.

# import hashlib
# from datetime import datetime, timedelta

# import mock

# import odoo.tests.common as common

# from odoo.addons.queue_job import identity_exact
# from odoo.addons.queue_job.exception import (
#    FailedJobError,
#    NoSuchJobError,
#    RetryableJobError,
# )
# from odoo.addons.queue_job.job import (
#    DONE,
#    ENQUEUED,
#    FAILED,
#    PENDING,
#    RETRY_INTERVAL,
#    STARTED,
#    Job,
# )

from .common import JobCommonCase


class TestJobsOnComputeFieldMethod(JobCommonCase):
    """Test Job on Compute Fields"""

    def test_01_create_registrant(self):
        self.registrant_1 = self.env["res.partner"].create(
            {
                "family_name": "Jaddranka",
                "given_name": "Heidi",
                "name": "Heidi Jaddranka",
                "is_group": False,
                "is_registrant": True,
            }
        )
