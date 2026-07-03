/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { FileUploader } from "@web/views/fields/file_handler";
import { Component } from "@odoo/owl";

export class InvoiceUploader extends Component {
    static template = "vendor_bill_ocr_automation.InvoiceUploader";
    static components = { FileUploader };

    static props = {
        ...standardWidgetProps,
        acceptedFileExtensions: { type: String, optional: true },
        record: { type: Object, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
    }

    async onFileUploaded(file) {
        const fileData = file?.data || file?.content || file?.base64;
        const resId = this.props.record?.resId || this.props.record?.data?.id;

        if (!fileData || !resId) {
            this.notification.add("Invalid file or record data.", { type: "danger" });
            return;
        }

        try {
            const result = await this.orm.call(
                "purchase.order",
                "action_upload_invoice",
                [[resId], file.name, file.type, fileData]
            );

            if (result?.type === "ir.actions.act_window") {
                await this.action.doAction(result);
            }
        } catch (error) {
            this.notification.add("OCR processing failed. Please try again.", { type: "danger" });
        }
    }
}

registry.category("view_widgets").add("invoice_uploader", {
    component: InvoiceUploader,
});