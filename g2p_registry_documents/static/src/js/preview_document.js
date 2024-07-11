/** @odoo-module **/
import {Component, xml} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";
import {useService} from "@web/core/utils/hooks";

class Widgetpreview extends Component {
    static template = xml`<button class="btn btn-primary" icon="fa-file-text-o" t-on-click="clickPreview">Preview</button>`;

    setup() {
        super.setup();
        this.fileViewer = useFileViewer();
        this.store = useService("mail.store");
        this.rpc = useService("rpc");
    }

    clickPreview(ev) {
        const currentRow = ev.target.closest(".o_data_row");
        if (currentRow) {
            const slugElement = currentRow.querySelector('.o_data_cell[name="slug"]');
            if (slugElement) {
                const slugValue = slugElement.textContent.trim();
                console.log("Slug Value:", slugValue);

                let recordID = 0;
                if (slugValue.includes("-")) {
                    const parts = slugValue.split("-");
                    const lastPart = parts[parts.length - 1].split(".")[0];
                    if (!isNaN(lastPart)) {
                        recordID = parseInt(lastPart, 10);
                    }
                }
                if (recordID) {
                    this._onPreviewButtonClick(recordID);
                }
            }
        }
    }

    async _onPreviewButtonClick(recordID) {
        const result = await this.rpc("/web/dataset/call_kw/storage.file/get_record", {
            model: "storage.file",
            method: "get_record",
            args: [[recordID]],
            kwargs: {},
        });
        const mimetype = result.mimetype;

        const file = {
            id: recordID,
            displayName: result.name,
            downloadUrl: result.url,
            isViewable: mimetype.includes("image") || mimetype.includes("pdf"),
            defaultSource: result.url,
            isImage: mimetype.includes("image"),
            isPdf: mimetype.includes("pdf"),
        };
        if (file.isViewable) {
            this.fileViewer.open(file);
        } else {
            window.open(result.url, "_blank");
        }
    }
}

registry.category("view_widgets").add("action_preview", {component: Widgetpreview});
