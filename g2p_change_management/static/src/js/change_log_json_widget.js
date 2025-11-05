/** @odoo-module **/
import {Component, markup} from "@odoo/owl";
import {registry} from "@web/core/registry";

export class ChangeLogJsonWidget extends Component {
    static template = "g2p_change_management.ChangeLogJsonWidget";

    renderjson() {
        const jsonValue = this.props.record?.data?.[this.props.name];

        if (!jsonValue || jsonValue === "") {
            return {};
        }

        try {
            if (Array.isArray(jsonValue)) {
                const formatted = {};
                jsonValue.forEach((el, idx) => {
                    const key = el?.name || `section_${idx}`;
                    formatted[key] = this.flattenJson(el?.data || el);
                });
                return formatted;
            }

            return this.flattenJson(jsonValue);
        } catch (err) {
            console.error("renderjson error:", err);
            return {};
        }
    }

    isPlainObject(obj) {
        return (
            obj !== null &&
            typeof obj === "object" &&
            !Array.isArray(obj) &&
            Object.prototype.toString.call(obj) === "[object Object]" &&
            Object.getPrototypeOf(obj) === Object.prototype
        );
    }

    isDocumentList(value) {
        return (
            Array.isArray(value) &&
            value.length > 0 &&
            typeof value[0] === "object" &&
            value[0] !== null &&
            "document_id" in value[0]
        );
    }

    formatDocumentList(documents) {
        const host = window.location.origin;
        let documentFiles = "";

        for (let i = 0; i < documents.length; i++) {
            const document_slug = documents[i].document_slug;
            if (document_slug) {
                if (i > 0) {
                    documentFiles += `<br />`;
                }
                documentFiles += `<a href="${host}/storage.file/${document_slug}" target="_blank">${document_slug}<span class="fa fa-fw fa-external-link"></span></a>`;
            }
        }

        return markup(documentFiles);
    }

    parseJsonString(jsonString) {
        try {
            return JSON.parse(jsonString);
        } catch (err) {
            console.error("JSON parse error:", err);
            return {};
        }
    }

    convertArrayToObject(arr) {
        const converted = {};
        arr.forEach((val, idx) => {
            converted[idx] = typeof val === "object" && val !== null ? this.flattenJson(val) : val;
        });
        return converted;
    }

    processObjectValue(key, value) {
        if (this.isDocumentList(value)) {
            return this.formatDocumentList(value);
        }
        if (this.isPlainObject(value)) {
            return this.flattenJson(value);
        }
        if (typeof value === "object" && value !== null) {
            return value;
        }
        return value;
    }

    flattenJson(object) {
        if (!object || object === "") {
            return {};
        }

        let jsonObject = object;
        if (typeof object === "string") {
            jsonObject = this.parseJsonString(object);
            if (!jsonObject || Object.keys(jsonObject).length === 0) {
                return {};
            }
        }

        if (Array.isArray(jsonObject)) {
            return this.convertArrayToObject(jsonObject);
        }

        if (typeof jsonObject !== "object") {
            return {};
        }

        const result = {};
        for (const key in jsonObject) {
            if (!jsonObject[key]) {
                continue;
            }
            result[key] = this.processObjectValue(key, jsonObject[key]);
        }
        return result;
    }
}

export const changeLogJsonWidget = {
    component: ChangeLogJsonWidget,
    supportedTypes: ["jsonb", "text", "html"],
};
registry.category("fields").add("change_log_json_widget", changeLogJsonWidget);
