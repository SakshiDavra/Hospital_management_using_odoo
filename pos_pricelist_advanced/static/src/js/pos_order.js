/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

patch(PosOrder.prototype, {
    removeOrderline(line) {
        super.removeOrderline(...arguments);
        if (this.lines.length === 0) {
            const defaultPricelist = this.config?.pricelist_id || false;
            const currentId = this.pricelist_id?.id || false;
            const defaultId = defaultPricelist?.id || false;

            if (currentId !== defaultId) {
                this.setPricelist(defaultPricelist);
            }
        }
    },
});