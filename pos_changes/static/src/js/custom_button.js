/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";

patch(OrderWidget.prototype, {

    onClickClear() {
        const order = this.env.pos.get_order();
        if (order) {
            order.clear();
        }
    },

});