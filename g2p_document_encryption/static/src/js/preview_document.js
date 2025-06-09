/** @odoo-module **/
import {Widgetpreview} from "@g2p_documents/js/preview_document";
import {patch} from "@web/core/utils/patch";

patch(Widgetpreview.prototype, {
    setup() {
        super.setup(...arguments);
        this.canPreviewEncrypted = this.props.record.data.can_preview_encrypted;
    },
});
