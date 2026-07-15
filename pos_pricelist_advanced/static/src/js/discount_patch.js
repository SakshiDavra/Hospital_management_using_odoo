/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    async setDiscountFromUI(line, val) {
        const order = this.getOrder();
        const pricelist = order?.pricelist_id;

        if (pricelist && pricelist.maximum_discount && Number(val) > pricelist.maximum_discount) {
            this.dialog.add(AlertDialog, {
                title: _t("Maximum Discount"),
                body: _t(`You cannot apply more than ${pricelist.maximum_discount}% discount.`),
            });

            
            return;
        }
        return super.setDiscountFromUI(line, val);
    },
});
