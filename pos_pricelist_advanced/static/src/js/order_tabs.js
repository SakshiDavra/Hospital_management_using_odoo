/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { OrderTabs } from "@point_of_sale/app/components/order_tabs/order_tabs";

const originalNewFloatingOrder = OrderTabs.prototype.newFloatingOrder;

patch(OrderTabs.prototype, {
    async newFloatingOrder() {
        await this.pos.loadLatestPricelists();
        return await originalNewFloatingOrder.call(this);
    }
});