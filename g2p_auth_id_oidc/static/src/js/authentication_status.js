/** @odoo-module **/

import {Component} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export class RegIdAuthStatus extends Component {
    setup() {
        this.showWidget = Boolean(this.props.record.data.auth_oauth_provider_id);
        this.statusSelectionObject = Object.fromEntries(
            this.props.record.fields.authentication_status.selection
        );

        var self = this;
        this.props.record.model.orm
            .call(this.props.record.resModel, "get_auth_oauth_provider", [this.props.record.resId])
            .then((result) => {
                self.authProvider = result;
            });
    }

    renderStatus() {
        const status = this.props.record.data.authentication_status;
        return _t(this.statusSelectionObject[status]);
    }

    authenticateButtonClick() {
        const windowFeatures = `popup,height=${(screen.height * 2) / 3},width=${screen.width / 2}`;
        window.open(this.authProvider.auth_link, "", windowFeatures);
    }
}
RegIdAuthStatus.template = "g2p_auth_id_oidc.reg_id_auth_status";

export const regIdAuthStatusField = {
    component: RegIdAuthStatus,
    displayName: _t("Authentication Status"),
    supportedTypes: ["selection", "many2one", "char"],
    extractProps: ({decorations}) => {
        return {decorations};
    },
};

registry.category("fields").add("g2p_auth_id_oidc.reg_id_auth_status", regIdAuthStatusField);
