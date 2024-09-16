from . import models


def uninstall_hook(env):
    env["g2p.superset.dashboard.config"].search([]).unlink()
