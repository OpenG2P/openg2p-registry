/** @odoo-module */
import {Component, useState, useSubEnv} from "@odoo/owl";
import {getDefaultConfig} from "@web/views/view";
import {registry} from "@web/core/registry";

export class G2PSupersetDashboardEmbedded extends Component {
    setup() {
        this.state = useState({
            isLoading: true,
            dashboardUrl: "",
        });

        this.actionId = this.props.actionId;
        const orm = this.env.services.orm;

        useSubEnv({
            config: {
                ...getDefaultConfig(),
                ...this.env.config,
            },
        });

        this.loadDashboards(orm);
    }

    async loadDashboards(orm) {
        const data = await orm.searchRead(
            "g2p.superset.dashboard.config",
            [["action.id", "=", this.actionId]],
            ["url"],
            {limit: 1}
        );

        console.log(data[0].url);

        if (data && data.length > 0 && data[0].url) {
            this.superSetUrl = data[0].url;
        } else {
            this.superSetUrl = false;
        }

        this.state.isLoading = false;
    }
}

G2PSupersetDashboardEmbedded.template = "g2p_superset_dashboard.G2PSupersetDashboardEmbedded";
registry.category("actions").add("g2p.superset_dashboard_embedded", G2PSupersetDashboardEmbedded);
