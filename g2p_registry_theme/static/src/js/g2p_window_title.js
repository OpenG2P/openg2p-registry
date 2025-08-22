/** @odoo-module **/

import {WebClient} from "@web/webclient/webclient";
import {patch} from "@web/core/utils/patch";

patch(WebClient.prototype, {
    setup() {
        super.setup();
        this.title.setParts({zopenerp: "OpenG2P"});
    },
});
