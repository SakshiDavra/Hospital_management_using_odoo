/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";

patch(OrderSummary.prototype, {
    _setValue(val) {
        const result = super._setValue(...arguments);
        if (val === "remove") this.pos.recomputeBestPricelist(this.currentOrder);
        return result;
    },
});