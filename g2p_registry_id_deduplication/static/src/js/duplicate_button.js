/** @odoo-module **/

import {ListController} from "@web/views/list/list_controller";
import {patch} from "@web/core/utils/patch";
import {pick} from "@web/core/utils/objects";
import {useService} from "@web/core/utils/hooks";

patch(ListController.prototype, {
    setup() {
        super.setup();
        this.rpc = useService("rpc");
    },

    async click_deduplicate() {
        await this.env.onClickViewButton({
            clickParams: {
                name: "deduplicate_registrants",
                type: "object",
            },
            getResParams: () =>
                pick(this.model.root, "context", "evalContext", "resModel", "resId", "resIds"),
        });
    },
});
