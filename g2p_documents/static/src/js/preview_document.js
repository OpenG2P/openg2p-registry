/** @odoo-module **/
import {Component, xml} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";

class Widgetpreview extends Component {
    static template = xml`<button class="btn btn-primary" icon="fa-file-text-o" t-on-click="clickPreview">Preview</button>`;

    setup() {
        super.setup();
        this.fileViewer = useFileViewer();
    }

    clickPreview() {
        const recordData = this.props.record.data;
        const mimetype = recordData.mimetype;
        if (typeof mimetype === "string" && mimetype) {
            const file = {
                id: recordData.id,
                displayName: recordData.name,
                downloadUrl: recordData.url,
                isViewable: mimetype.includes("image") || mimetype.includes("pdf"),
                defaultSource: recordData.url,
                isImage: mimetype.includes("image"),
                isPdf: mimetype.includes("pdf"),
            };
            if (file.isViewable) {
                this.fileViewer.open(file);
            } else {
                window.open(recordData.url, "_blank");
            }
        } else {
            window.open(recordData.url, "_blank");
        }
    }
}

registry.category("view_widgets").add("g2p_documents_action_preview", {component: Widgetpreview});
