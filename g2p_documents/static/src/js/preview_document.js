/** @odoo-module **/

import {Component} from "@odoo/owl";
import {ConfirmationDialog} from "@web/core/confirmation_dialog/confirmation_dialog";
import {registry} from "@web/core/registry";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";
import {useService} from "@web/core/utils/hooks";

class Widgetpreview extends Component {
    setup() {
        this.dialog = useService("dialog");
        this.fileViewer = useFileViewer();
    }

    clickPreview() {
        const record = this.props.record?.data || {};
        const {id, name, url, mimetype = ""} = record;

        const isImage = mimetype.includes("image");
        const isPdf = mimetype.includes("pdf");

        if (isImage || isPdf) {
            this.fileViewer.open({
                id,
                displayName: name,
                downloadUrl: url,
                defaultSource: url,
                isViewable: true,
                isImage,
                isPdf,
            });
        } else if (url) {
            this.downloadUnPreviewedFile(url, name);
        }
    }

    downloadUnPreviewedFile(url, filename) {
        const fileName = filename || "file";

        this.dialog.add(ConfirmationDialog, {
            title: "File Not Previewable",
            body: `The file "${fileName}" cannot be previewed. Do you want to download it to access the file?`,
            confirmLabel: "Download",
            cancelLabel: "Cancel",
            confirm: () => {
                const a = document.createElement("a");
                a.href = url;
                a.setAttribute("download", fileName);
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            },
            cancel: () => {
                // User cancelled
            },
        });
    }
}

Widgetpreview.template = "g2p_documents.Widgetpreview";
registry.category("view_widgets").add("g2p_documents_action_preview", {
    component: Widgetpreview,
});
