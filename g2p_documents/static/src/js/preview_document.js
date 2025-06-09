/** @odoo-module **/
import {Component} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";

export class Widgetpreview extends Component {
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
Widgetpreview.template = "g2p_documents.Widgetpreview";

registry.category("view_widgets").add("g2p_documents_action_preview", {component: Widgetpreview});
