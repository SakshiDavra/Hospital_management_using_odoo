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

         model: { type: String, optional: true },
        listMode: { type: Boolean, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
    }

    async onFileUploaded(file) {

        const fileData = file?.data || file?.content || file?.base64;

        let resId = this.props.record?.resId || this.props.record?.data?.id;
        let model = this.props.record?.resModel || this.props.model;

        if (this.props.listMode === true) {
            resId = false;
        }

        if (!fileData || !model) {
            this.notification.add("Invalid file.", {
                type: "danger",
            });
            return;
        }

        try {
            const ids = resId ? [resId] : [];

            const result = await this.orm.call(
                model,
                "action_upload_invoice",
                [ids, file.name, file.type, fileData]
            );

            if (!result) {
                return;
            }

            if (result.tag === "display_notification") {
                if (this.props.record?.model?.root) {
                    await this.props.record.model.root.load();
                }
                return;
            }

            console.log("ACTION RESULT", result);

            await this.action.doAction(result);

        } catch (error) {

            this.notification.add(
                error?.message || "OCR processing failed.",
                { type: "danger" }
            );

            throw error;
        }
    }
}

registry.category("view_widgets").add("invoice_uploader", {
    component: InvoiceUploader,
});