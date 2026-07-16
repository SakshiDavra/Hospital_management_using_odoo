/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { CashierSelectionPopup } from "@pos_hr/app/components/popups/cashier_selection_popup/cashier_selection_popup";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    async sha1(value) {
        const hash = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(value));
        return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
    },
    async verifyManagerPinForPricelist(pricelist) {
        if (!pricelist.manager_pin_required) {
            return true;
        }
        const employees = this.models["hr.employee"]?.getAll() || [];
        const advancedEmployeeIds = (this.config.advanced_employee_ids || []).map((employee) => employee.id || employee);
        const approvers = employees.filter((employee) => advancedEmployeeIds.includes(employee.id) && employee._pin);
        
        if (!approvers.length) {
            this.dialog.add(AlertDialog, {
                title: _t("Access Denied"),
                body: _t("No authorized employee with a configured PIN was found."),
            });
            return false;
        }
        const approver = await makeAwaitable(this.dialog, CashierSelectionPopup, { employees: approvers });
        if (!approver) {
            return false;
        }
        if (!approver._pin) {
            this.dialog.add(AlertDialog, {
                title: _t("PIN Not Configured"),
                body: _t("The selected employee does not have a PIN configured."),
            });
            return false;
        }
        const pin = await makeAwaitable(this.dialog, NumberPopup, { title: _t("Manager PIN") });
        if (!pin) {
            return false;
        }
        const hashedPin = await this.sha1(pin);
        if (hashedPin !== approver._pin) {
            this.dialog.add(AlertDialog, {
                title: _t("Incorrect PIN"),
                body: _t("The PIN you entered is incorrect."),
            });
            return false;
        }
        return true;
    }
});
patch(ControlButtons.prototype, {
    async clickPricelist() {
        const pricelist = await makeAwaitable(this.dialog, SelectionPopup, {
            title: _t("Select Pricelist"),
            list: this.getPricelistList(),
        });
        if (!pricelist) {
            return;
        }
        const pinVerified = await this.pos.verifyManagerPinForPricelist(pricelist);
        if (pinVerified) {
            this.pos.selectPricelist(pricelist);
        }
    },
});