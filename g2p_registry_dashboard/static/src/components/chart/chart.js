/** @odoo-module */
/* global Chart */

import {Component, onMounted, onWillStart, useRef} from "@odoo/owl";
import {loadJS} from "@web/core/assets";

export class ChartComponent extends Component {
    setup() {
        this.canvasRef = useRef("canvas");

        onWillStart(async () => {
            await loadJS("https://cdn.jsdelivr.net/npm/chart.js");
        });

        onMounted(() => this.renderChart());
    }

    renderChart() {
        const ctx = this.canvasRef.el.getContext("2d");

        // eslint-disable-next-line no-new
        new Chart(ctx, {
            type: this.props.type,
            data: {
                labels: this.props.labels,
                datasets: [
                    {
                        label: this.props.data_label,
                        data: this.props.data,
                        backgroundColor: this.props.backgroundColor,
                        hoverOffset: 2,
                    },
                ],
            },
            options: {...this.props.options},
        });
    }
}

ChartComponent.template = "g2p_registry_dashboard.ChartTemplate";

ChartComponent.props = {
    type: {type: String, optional: true},
    labels: {type: Array, optional: true},
    title: {type: String, optional: true},
    data_label: {type: String, optional: true},
    data: {type: Array, optional: true},
    backgroundColor: {type: Array, optional: true},
    options: {type: Object, optional: true},
    size: {type: String, optional: true},
};
