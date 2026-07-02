/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { FileUploader } from "@web/views/fields/file_handler";
import { Component } from "@odoo/owl";

export class InvoiceUploader extends Component {
    static template = "vendor_bill_ocr_automation.InvoiceUploader";

    static props = {
        ...standardWidgetProps,
        acceptedFileExtensions: { type: String, optional: true },
        record: { type: Object, optional: true },
        list: { type: Object, optional: true },
    };
    static components = { FileUploader };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.attachmentIdsToProcess = [];
    }

    async getIds() {
        if (this.props.record) {
            return this.props.record.data.id;
        }
        return this.props.list.getResIds(true);
    }

    async onFileUploaded(file) {
        const attachmentData = {
            name: file.name,
            mimetype: file.type,
            datas: file.data,
        };
        const [attachmentId] = await this.orm.create("ir.attachment", [attachmentData]);
        this.attachmentIdsToProcess.push(attachmentId);
    }

    async onUploadComplete() {
        const ids = await this.getIds();
        let action;

        try {
            action = await this.orm.call("purchase.order", "action_upload_invoice", [ids, this.attachmentIdsToProcess]);
        } finally {
            this.attachmentIdsToProcess = []; 
        }

        if (action) {
            this.action.doAction(action);
        }
    }
}

export const invoiceUploader = { component: InvoiceUploader };
registry.category("view_widgets").add("invoice_uploader", invoiceUploader);