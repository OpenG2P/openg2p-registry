/** @odoo-module **/

import {textField} from "@web/views/fields/text/text_field";
import {registry} from "@web/core/registry";
import {qweb} from "web.core";

// TODO: Have to changes this widget to odoo17 verison
var G2PRegAdditionalInfoWidget = textField.extend({
    className: "o_field_g2p_addl_info",
    supportedFieldTypes: ["json", "text", "html"],
    tagName: "div",
    _renderReadonly: function () {
        try {
            let valuesJsonOrig = this.value;
            if (typeof valuesJsonOrig === "string" || valuesJsonOrig instanceof String) {
                valuesJsonOrig = JSON.parse(this.value);
            }

            if (Array.isArray(valuesJsonOrig)) {
                const sectionsJson = {};
                var self = this;
                valuesJsonOrig.forEach((element) => {
                    sectionsJson[element.name] = self.flattenJson(element.data);
                });
                return this.$el.html(
                    qweb.render("addl_info_template", {
                        sections: sectionsJson,
                    })
                );
            }

            const valuesJson = this.flattenJson(valuesJsonOrig);
            return this.$el.html(
                qweb.render("addl_info_each_table", {
                    flatJson: valuesJson,
                })
            );
        } catch (err) {
            console.error(err);
        }
        return this._super();
    },
    flattenJson: function (object) {
        const jsonObject = JSON.parse(JSON.stringify(object));
        for (const key in jsonObject) {
            if (typeof jsonObject[key] === "object") {
                jsonObject[key] = JSON.stringify(jsonObject[key]);
            }
        }
        return jsonObject;
    },
    _isSameValue: function (value) {
        return _.isEqual(value, this.value);
    },
});

registry.category("fields").add("g2p_registry_addl_info_widget", G2PRegAdditionalInfoWidget);
