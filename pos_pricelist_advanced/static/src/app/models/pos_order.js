/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";

patch(PosOrder.prototype, {
    async removeOrderline(line) {
        super.removeOrderline(...arguments);
        if (this.lines.length === 0) await this.pos.recomputeBestPricelist(this);
    },
});