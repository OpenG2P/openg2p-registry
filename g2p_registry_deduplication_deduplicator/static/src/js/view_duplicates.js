/** @odoo-module **/

import {Component, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class ViewDeduplicatorDuplicates extends Component {
    setup() {
        this.recordId = this.props.action.params.record_id;

        this.state = useState({dataLoading: "not_loaded"});
        this.displayError = "";
        this.duplicatesData = [];

        this.ormService = useService("orm");
        const self = this;
        this.ormService
            .call("g2p.registry.deduplication.deduplicator.config", "get_duplicates_by_record_id", [
                this.recordId,
            ])
            .then((res) => {
                self.duplicatesData = res;
                self.state.dataLoading = "loaded";
            })
            .catch((err) => {
                console.error("Cannot retrieve duplicates", err);
                self.displayError = _t("Cannot retrieve duplicates") + err;
                self.state.dataLoading = "error";
            });
    }
}

ViewDeduplicatorDuplicates.template = "g2p_registry_deduplicator_view_duplicates_tpl";

registry
    .category("actions")
    .add("g2p_registry_deduplication_deduplicator.view_duplicates_client_action", ViewDeduplicatorDuplicates);
