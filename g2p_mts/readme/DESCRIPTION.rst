Description
===========

* This module is an extension to MTS Connector (`mts_connector`) module.
* This module adds the following input type to MTS Connectors:
    * `OpenG2P Registry` itself can now become input to MTS. (This overloads the `Custom` input from original module).
* This also adds additional configuration to filter out what data from the registry is to be sent to MTS.
* This adds another recurring job to delete any VIDs, for which the UIN Token has already been processed, from
  the registry. This can be configured in the Settings pane.
* Refer to the documentation `here <https://docs.openg2p.org/integrations/integration-with-mosip/registry-mts-connector>`_.
