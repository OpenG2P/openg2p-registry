/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {TextField} from "@web/views/fields/text/text_field";
import {useState} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export class JsonFieldWidgets extends TextField {

    setup() {
        super.setup();
        this.state = useState({recordClicked: false, issueRaised: false});
        this.notification = useService("notification");
    }

    onclick(event) {
        if (this.editingRecord && event) {
            this.state.recordClicked = true;
        } else {
            this.state.recordClicked = false;
        }
    }

    get editingRecord() {
        return !this.props.readonly;
    }

    get renderjson() {
        try {
            let valuesJsonOrig = this.props.record.data.additional_g2p_info;
            if (typeof valuesJsonOrig === "string" || valuesJsonOrig instanceof String) {
                valuesJsonOrig = JSON?.parse(valuesJsonOrig);
            }

            if (Array.isArray(valuesJsonOrig)) {
                const sectionsJson = {};
                valuesJsonOrig.forEach((element) => {
                    sectionsJson[element.name] = this.flattenJson(element.data);
                });

                return sectionsJson;
            } else {
                const valuesJson = this.flattenJson(valuesJsonOrig);
                return valuesJson;
            }
        } catch (err) {
            this.notification.add(_t("Additional Information"), {
                title: _t("Invalid Json Value"),
                type: "danger",
                sticky: true,
            });
            this.state.recordClicked = true;
            this.state.issueRaised = true;
            return {};
        }
    }

    flattenJson(object) {
        const jsonObject = JSON?.parse(JSON?.stringify(object));
        for (const key in jsonObject) {
            if (typeof jsonObject[key] === "object") {
                jsonObject[key] = JSON?.stringify(jsonObject[key]);
            }
        }
        return jsonObject;
    }
}
JsonFieldWidgets.template = addl_info_each_table;

export const jsonFieldWidgets = {
    component: JsonFieldWidgets,
    supportedTypes: ["json", "text", "html"],
};

registry.category("fields").add("g2p_registry_addl_info_widget", jsonFieldWidgets);
