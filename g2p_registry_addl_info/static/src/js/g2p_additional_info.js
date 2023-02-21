/** @odoo-module **/

import {FieldText} from "web.basic_fields";
import fieldsRegistry from "web.field_registry";
import {qweb} from "web.core";

var G2PAdditionalInfoWidget = FieldText.extend({
    className: "o_field_g2p_addl_info",
    _render: function () {
        if (this.mode === "edit") {
            if (this.value) {
                try {
                    this.value = JSON.stringify(JSON.parse(this.value), null, 2);
                } catch (err) {
                    // Pass value as is, when error
                    console.error(err);
                }
            }
            return this._super();
        }
        try {
            const valuesJson = JSON.parse(this.value);
            let sections = {};
            for (const key in valuesJson) {
                if (typeof valuesJson[key] === "object") {
                    sections[key] = this.flattenJson(valuesJson[key]);
                    delete valuesJson[key];
                }
            }
            if (Object.keys(sections).length === 0) {
                sections = false;
            }
            console.debug(sections);
            console.debug(valuesJson);
            return this.$el.html(
                qweb.render("addl_info_template", {
                    sections: sections,
                    values: valuesJson,
                })
            );
        } catch (err) {
            console.error(err);
            return this._super();
        }
    },
    flattenJson: function (jsonObject) {
        for (const key in jsonObject) {
            if (typeof jsonObject[key] === "object") {
                jsonObject[key] = JSON.stringify(jsonObject[key]);
            }
        }
        return jsonObject;
    },
});

fieldsRegistry.add("g2p_addl_info_widget", G2PAdditionalInfoWidget);

export {G2PAdditionalInfoWidget};
