/** @odoo-module */
import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";

export class G2PSupersetDashboardEmbedded extends Component {
    setup() {
        this.state = useState({
            isLoading: true,
            dashboards: [],
            dashboardUrl: "",
        });

        const orm = this.env.services.orm;
        this.loadDashboards(orm);
    }

    async loadDashboards(orm) {
        // Fetch dashboard configurations
        const dashboardData = await orm.searchRead("g2p.superset.dashboard.config", [], ["name", "url"]);
        this.state.dashboards = dashboardData;

        if (dashboardData.length > 0) {
            this.state.dashboardUrl = dashboardData[0].url;
        }

        this.state.isLoading = false;
    }

    onDashboardSelect(event) {
        const selectedUrl = event.target.value;
        this.state.dashboardUrl = selectedUrl;
    }
}

G2PSupersetDashboardEmbedded.template = "g2p_superset_dashboard.G2PSupersetDashboardEmbedded";
registry.category("actions").add("g2p.superset_dashboard_embedded", G2PSupersetDashboardEmbedded);
