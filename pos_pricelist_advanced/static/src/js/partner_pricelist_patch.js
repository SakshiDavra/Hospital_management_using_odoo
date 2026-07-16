/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { isPricelistValid } from "./pricelist_utils";

patch(PosStore.prototype, {
    async setPartnerToCurrentOrder(partner) {
        const order = this.getOrder();
        const previousPricelist = order?.pricelist_id || this.config.pricelist_id;
        super.setPartnerToCurrentOrder(...arguments);
        if (!partner || !order) {
            return;
        }

        const customerPricelist = order.pricelist_id;
        if (!customerPricelist) {
            return;
        }

        order.setPricelist(previousPricelist);
        if (!isPricelistValid(customerPricelist)) {
            this.dialog.add(AlertDialog, {
                title: _t("Pricelist Inactive"),
                body: _t("The pricelist assigned to this customer is not active or approved."),
            });
            return;
        }
        const allowed = await this.verifyManagerPinForPricelist(customerPricelist);
        if (!allowed) {
            return;
        }
        order.setPricelist(customerPricelist);
    },
});