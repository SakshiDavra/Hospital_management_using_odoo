/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { LocationPopup } from "./location_popup";

patch(ProductScreen.prototype, {

    async addProductToOrder(product) {

        const locations = this.pos.data["stock.location"] || [];

        console.log("LOCATIONS:", locations);

        const result = await new Promise((resolve) => {
            this.dialog.add(LocationPopup, {
                locations: locations,
                close: resolve,
            });
        });

        if (!result || !result.confirmed) {
            return;
        }

        await super.addProductToOrder(...arguments);

        const order = this.pos.getOrder();
        const line = order.getLastOrderline();

        if (line) {
            line.location_id = result.location.id;
        }
    }

});