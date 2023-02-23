/** @odoo-module **/

import {FieldText} from "web.basic_fields";
import field_utils from "web.field_utils";
import fieldsRegistry from "web.field_registry";
import {qweb} from "web.core";

field_utils.format.json = function (value) {
    return JSON.stringify(value, null, 2);
};
field_utils.parse.json = function (value) {
    return JSON.parse(value);
};

var G2PAdditionalInfoWidget = FieldText.extend({
    className: "o_field_g2p_addl_info",
    supportedFieldTypes: ["json", "text", "html"],
    tagName: "div",
    _renderReadonly: function () {
        try {
            let valuesJsonOrig = this.value;

            if (typeof valuesJsonOrig === "string" || valuesJsonOrig instanceof String) {
                valuesJsonOrig = JSON.parse(this.value);
            }
            const valuesJson = {};
            let sections = {};
            for (const key in valuesJsonOrig) {
                if (typeof valuesJsonOrig[key] === "object") {
                    sections[key] = this.flattenJson(valuesJsonOrig[key]);
                } else {
                    valuesJson[key] = valuesJsonOrig[key];
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

fieldsRegistry.add("g2p_addl_info_widget", G2PAdditionalInfoWidget);

export {G2PAdditionalInfoWidget};
