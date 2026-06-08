/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {
    setup() {
        super.setup();
        if (this.props.resModel !== "password.view.wizard") {
            return;
        }
        const timeout = (this.props.context?.auto_close_timeout || 10) * 1000;
        this.passwordAutoCloseTimer = setTimeout(() => {
            const closeBtn = document.querySelector(".modal .btn-close, .modal .o_dialog_close");

            if (closeBtn) {closeBtn.click();}
        }, timeout);
    },
    willUnmount() {
        super.willUnmount?.();
        if (this.passwordAutoCloseTimer) {
            clearTimeout(this.passwordAutoCloseTimer);
        }
    },
});