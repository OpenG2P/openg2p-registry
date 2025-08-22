/** @odoo-module */

import {G2PLeafletMapController} from "./g2p_lmap_controller";
import {registry} from "@web/core/registry";

const g2pLeafletMapView = {
    type: "lmap",
    display_name: "Leaflet Map",
    icon: "fa fa-map-marker",
    multiRecord: true,
    Controller: G2PLeafletMapController,
};

registry.category("views").add("lmap", g2pLeafletMapView);
