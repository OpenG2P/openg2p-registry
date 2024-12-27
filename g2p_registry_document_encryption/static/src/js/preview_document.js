/** @odoo-module **/
import {Component, onWillStart, xml} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";
import {useService} from "@web/core/utils/hooks";

// Unregister the existing widget (if any)
registry.category("view_widgets").remove("action_preview");

class Widgetpreview extends Component {
    static template = xml`
        <t>
            <button
                class="btn btn-primary"
                icon="fa-file-text-o"
                t-on-click="clickPreview"
                t-if="canPreview"
            >
                Preview
            </button>
            <span t-else="">Encrypted</span>
        </t>
    `;

    setup() {
        super.setup();
        this.fileViewer = useFileViewer();
        this.store = useService("mail.store");
        this.rpc = useService("rpc");

        // Fetch and check the decrypt registry value on start
        onWillStart(async () => {
            this.decryptRegistry = await this._getDecryptRegistryValue();
            this.canPreview = this._checkPreviewConditions();
        });
    }

    // Fetch the decryption parameter from the ir.config_parameter model
    async _getDecryptRegistryValue() {
        const result = await this.rpc("/web/dataset/call_kw/ir.config_parameter/get_param", {
            model: "ir.config_parameter",
            method: "get_param",
            args: ["g2p_registry_encryption.decrypt_registry"],
            kwargs: {},
        });
        return result === "True";
    }

    // Check conditions for enabling the preview button
    _checkPreviewConditions() {
        const is_encrypted = this.props.record.data.is_encrypted;
        const decrypt_registry = this.decryptRegistry;
        return !is_encrypted || (is_encrypted && decrypt_registry);
    }

    // Handle preview button click
    clickPreview(ev) {
        const currentRow = ev.target.closest(".o_data_row");
        if (currentRow) {
            const slugElement = currentRow.querySelector('.o_data_cell[name="slug"]');
            if (slugElement) {
                const slugValue = slugElement.textContent.trim();

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

    // Fetch the record and show the preview
    async _onPreviewButtonClick(recordID) {
        const result = await this.rpc("/web/dataset/call_kw/storage.file/get_record", {
            model: "storage.file",
            method: "get_record",
            args: [[recordID]],
            kwargs: {},
        });
        const mimetype = result.mimetype;
        if (typeof mimetype === "string" && mimetype) {
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
        } else {
            window.open(result.url, "_blank");
        }
    }
}

// Register the new widget to replace the existing one
registry.category("view_widgets").add("action_preview", {component: Widgetpreview});
