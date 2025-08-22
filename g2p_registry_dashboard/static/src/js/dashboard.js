/** @odoo-module **/
import {Component, useState} from "@odoo/owl";
import {ChartComponent} from "../components/chart/chart";
import {KpiComponent} from "../components/kpi/kpi";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

class G2PRegistryDashboard extends Component {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.dashboard_title = "Registry Dashboard";

        this.dashboard_data = useState({
            total_groups: 0,
            total_individuals: 0,
            gender_distribution_keys: [],
            gender_distribution_values: [],
            age_distribution_keys: [],
            age_distribution_values: [],
        });

        this.dataLoaded = useState({flag: false});

        this.fetchData();
    }

    async fetchData() {
        try {
            const data = await this.orm.call("res.partner", "get_dashboard_data", []);

            data.gender_distribution_keys = Object.keys(data.gender_distribution);
            data.gender_distribution_values = Object.values(data.gender_distribution);
            data.age_distribution_keys = Object.keys(data.age_distribution);
            data.age_distribution_values = Object.values(data.age_distribution);

            Object.assign(this.dashboard_data, data);

            this.dataLoaded.flag = true;
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        }
    }
}

G2PRegistryDashboard.template = "g2p_registry_dashboard.dashboard_template";
G2PRegistryDashboard.components = {ChartComponent, KpiComponent};

registry.category("actions").add("g2p_registry_dashboard.g2p_registry_dashboard_tag", G2PRegistryDashboard);
