/** @odoo-module */

import {Component} from "@odoo/owl";
import {G2PLeafletMapRenderer} from "./g2p_lmap_renderer";
import {Layout} from "@web/search/layout";
import {standardViewProps} from "@web/views/standard_view_props";

export class G2PLeafletMapController extends Component {
    static template = "g2p_leaflet_map.MapView";
    static components = {G2PLeafletMapRenderer, Layout};
    static props = {
        ...standardViewProps,
    };

    setup() {
        console.log(this);
        this.polygonCoords = this.props.context?.polygon_coords || [];
        this.partnerLatitude = this.props.context?.partner_latitiude || null;
        this.partnerLongitude = this.props.context?.partner_longitude || null;
    }
}
