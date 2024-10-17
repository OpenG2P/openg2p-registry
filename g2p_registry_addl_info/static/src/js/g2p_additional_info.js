/** @odoo-module **/

import {markup, useRef, useState} from "@odoo/owl";
import {TextField} from "@web/views/fields/text/text_field";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class G2PRegistryAddlInfoComponent extends TextField {
    static template = "g2p_reg_addl_info_tpl";

    setup() {
        super.setup();
        this.state = useState({editingMode: false});
        this.textareaRef = useRef("textarea");
        this.notification = useService("notification");
    }

    editButtonClick() {
        const val = this.props.record.data[this.props.name];
        if (typeof val !== "string") {
            this.props.record.data[this.props.name] = JSON.stringify(val);
        }
        this.state.editingMode = true;
    }

    doneButtonClick() {
        let val = null;
        try {
            val = JSON.parse(this.textareaRef.el.value);
        } catch (err) {
            this.notification.add(_t("Registry Additional Info"), {
                title: _t("Invalid Json Value"),
                type: "danger",
            });
            console.error(err);
            return;
        }
        try {
            this.props.record.update({[this.props.name]: val});
            this.state.editingMode = false;
        } catch (err) {
            this.notification.add(_t("Registry Additional Info"), {
                title: _t("Error Updating Json"),
                type: "danger",
            });
            console.error(err);
        }
    }

    renderjson() {
        const valuesJsonOrig = this.props.record.data[this.props.name];
        try {
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
            console.error(err);
            this.notification.add(_t("Registry Additional Info"), {
                title: _t("Invalid Json Value"),
                type: "danger",
            });
            this.state.editingMode = true;
            return {};
        }
    }

    flattenJson(object) {
        let jsonObject = object;
        if (typeof object === "string") {
            jsonObject = JSON.parse(object);
        }
        for (const key in jsonObject) {
            if (!jsonObject[key]) {
                continue;
            } else if (
                Array.isArray(jsonObject[key]) &&
                jsonObject[key].length > 0 &&
                typeof jsonObject[key][0] === "object" &&
                "document_id" in jsonObject[key][0] &&
                "document_slug" in jsonObject[key][0]
            ) {
                var documentFiles = "";
                for (var i = 0; i < jsonObject[key].length; i++) {
                    const document_slug = jsonObject[key][i].document_slug;
                    const host = window.location.origin;
                    if (i > 0) {
                        documentFiles += `<br />`;
                    }
                    documentFiles += `<a href="${host}/storage.file/${document_slug}" target="_blank">${document_slug}<span class="fa fa-fw fa-external-link"></span></a>`;
                }
                jsonObject[key] = markup(documentFiles);
            } else if (typeof jsonObject[key] === "object") {
                jsonObject[key] = this.flattenJson(jsonObject[key]);
            }
        }
        return jsonObject;
    }
}

export const g2pRegistryAddlInfoWidget = {
    component: G2PRegistryAddlInfoComponent,
    supportedTypes: ["jsonb", "text", "html"],
};
registry.category("fields").add("g2p_registry_addl_info_widget", g2pRegistryAddlInfoWidget);
