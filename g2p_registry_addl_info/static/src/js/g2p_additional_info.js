/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {onMounted, useExternalListener, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {TextField} from "@web/views/fields/text/text_field";
import {useService} from "@web/core/utils/hooks";

export class JsonFieldWidget extends TextField {
    setup() {
        super.setup();
        this.state = useState({recordClicked: false, noValue: false});
        this.notification = useService("notification");
        onMounted(() => this.validateValue());
        useExternalListener(window, "click", this.onclick);
        useExternalListener(window, "mouseup", this.onMouseup);
    }

    getValue() {
        const value = this.props.record.data.additional_g2p_info;
        if (!value || !(value.length > 0)) {
            this.state.noValue = true;
        }
        this.validateValue();
    }

    validateValue() {
        const val = this.props.record.data.additional_g2p_info;
        if (val) {
            if ((!(val.charAt(0) === "{") && !(val.charAt(val.length - 1) === "}")) || !val) {
                this.state.noValue = true;
            }
        } else {
            this.state.noValue = true;
        }
    }

    onclick(event) {
        if (this.editingRecord && event.target.closest(".json-widget")) {
            this.state.recordClicked = true;
            this.state.noValue = true;
        }
        this.validateValue();
    }

    onMouseup(ev) {
        if (!ev.target.closest(".o_field_g2p_registry_addl_info_widget textarea")) {
            this.state.recordClicked = false;
            this.state.noValue = false;
        }
        this.validateValue();
    }

    get editingRecord() {
        return !this.props.readonly;
    }

    renderjson() {
        try {
            const valuesJsonOrig = this.props.record.data.additional_g2p_info;
            if (typeof valuesJsonOrig === "string" || valuesJsonOrig instanceof String) {
                const parsedValue = JSON.parse(valuesJsonOrig);
                return parsedValue;
            }

            if (Array.isArray(valuesJsonOrig)) {
                const sectionsJson = {};
                valuesJsonOrig.forEach((element) => {
                    sectionsJson[element.name] = this.flattenJson(element.data);
                });
                return sectionsJson;
            }
            const valuesJson = this.flattenJson(valuesJsonOrig);
            return valuesJson;
        } catch (err) {
            this.notification.add(_t("Additional Information"), {
                title: _t("Invalid Json Value"),
                type: "danger",
            });
            this.state.recordClicked = true;
            return {};
        }
    }

    flattenJson(object) {
        const jsonObject = JSON.parse(JSON.stringify(object));
        for (const key in jsonObject) {
            if (typeof jsonObject[key] === "object") {
                jsonObject[key] = JSON.stringify(jsonObject[key]);
            }
        }
        return jsonObject;
    }
}

JsonFieldWidget.template = "addl_info_each_table";

export const JsonField = {
    component: JsonFieldWidget,
    supportedTypes: ["json", "text", "html"],
};

registry.category("fields").add("g2p_registry_addl_info_widget", JsonField);
