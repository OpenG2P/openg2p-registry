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
                }
            }
            return this._super();
        }
        try {
            const values_json = JSON.parse(this.value);
            for (const key in values_json) {
                if (typeof values_json[key] === "object") {
                    values_json[key] = JSON.stringify(values_json[key]);
                }
            }
            return this.$el.html(
                qweb.render("g2p.addl.info.template", {
                    value: values_json,
                })
            );
        } catch (err) {
            return this._super();
        }
    },
});

fieldsRegistry.add("g2p_addl_info_widget", G2PAdditionalInfoWidget);

export {G2PAdditionalInfoWidget};
