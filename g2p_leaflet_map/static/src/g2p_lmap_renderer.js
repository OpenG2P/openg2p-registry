/** @odoo-module */
/* global L */

import {Component, onMounted, onWillStart, useRef} from "@odoo/owl";
import {loadCSS, loadJS} from "@web/core/assets";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";

export class G2PLeafletMapRenderer extends Component {
    static template = "g2p_leaflet_map.MapRenderer";

    static props = {
        polygonCoords: {type: Array, optional: true, default: []},
        partnerLatitude: {type: Number, optional: true},
        partnerLongitude: {type: Number, optional: true},
    };

    setup() {
        console.log("Renderer Props:", this.props);
        this.root = useRef("map");

        onWillStart(async () => {
            try {
                const response = await fetch("/osm/config/get", {
                    method: "GET",
                    headers: {"Content-Type": "application/json"},
                });

                if (response.ok) {
                    const data = await response.json();
                    this.tile_server_url = data?.tile_server_url;
                } else {
                    this.tile_server_url = null;
                    console.warn("Failed to fetch tile server URL, using default.");
                }

                await loadCSS("/g2p_leaflet_map/static/lib/leaflet/leaflet.css");
                await loadJS("/g2p_leaflet_map/static/lib/leaflet/leaflet.js");
            } catch (error) {
                console.error("Error loading OSM config:", error);
            }
        });

        onMounted(() => {
            if (!this.root.el) return;

            if (typeof L === "undefined") {
                console.error("Leaflet JS is not loaded.");
                return;
            }

            if (!this.tile_server_url) {
                // Console.error("Map not JS is not loaded.");
                return this.showDialog();
            }

            const mapCenter = [9.145, 40.489];
            const zoomLevel = 12;
            this.map = L.map(this.root.el).setView(mapCenter, zoomLevel);

            L.tileLayer(this.tile_server_url, {
                maxZoom: 19,
                attribution: "&copy; OpenStreetMap contributors",
            }).addTo(this.map);

            const bounds = L.latLngBounds([]);

            const colors = ["blue", "green", "red", "purple", "orange", "yellow"];

            // **Add Polygons from Land Data**
            if (this.props.polygonCoords?.length) {
                this.props.polygonCoords.forEach((land, index) => {
                    const polygonColor = colors[index % colors.length];

                    const polygon = L.polygon(land.polygon_data, {
                        color: polygonColor,
                        fillColor: polygonColor,
                        fillOpacity: 0.5,
                    }).addTo(this.map);

                    bounds.extend(polygon.getBounds());
                });
            } else {
                console.warn("No land data received.");
            }

            if (bounds.isValid()) {
                this.map.fitBounds(bounds.pad(0.2));
            } else {
                this.map.setView(mapCenter, zoomLevel);
            }
        });
    }

    showDialog() {
        const dialog = this.env.services.dialog;
        dialog.add(ConfirmationDialog, {
            title: "Map Configuration Error",
            body: "No Map Tile server Configuration Found!",
        });

        return dialog;
    }
}
