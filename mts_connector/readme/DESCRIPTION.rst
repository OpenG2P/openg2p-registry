Description
===========

* This module provides interfaces to connect to MOSIP Token Seeder.
* MOSIP Token Seeder has to be installed seperately so that this module can connect to it.
* Multiple Connectors can be configured, and each connector can be configured to run in `Recurring` mode or `Onetime` mode, with relevant configurations.
* This module currently supports following input types:
    * `ODK`
    * `Custom` (This is to be overloaded by other modules)
* This module currently supports following delivery types:
    * `Callback`
* Refer to the documentation `here <https://docs.openg2p.org/integrations/integration-with-mosip/mts-connector>`_.
