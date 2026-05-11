/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {

    async setup() {

        await super.setup(...arguments);

        const rawQuants = this.models["stock.quant"].getAll();
        const locations =
            this.models["stock.location"]
                .getAll()
                .filter(
                    loc => loc.usage === "internal"
                );
        const locationMap = Object.fromEntries(
            locations.map(loc => [
                loc.id,
                loc.complete_name || loc.name
            ])
        );
        this.productStockMap = {};

        rawQuants.forEach((quant) => {
            if (!quant?.product_id || !quant?.location_id) {
                return;
            }

            const pId = quant.product_id.id || quant.product_id;
            const locId = quant.location_id.id || quant.location_id;

            if (!locationMap[locId]) {
                return;
            }

            const qty = quant.quantity || 0;
            const stockLine = {
                locationId: locId,
                locationName: locationMap[locId] || "Unknown Location",
                stockQty: qty,
            };

            if (!this.productStockMap[pId]) {
                this.productStockMap[pId] = [];
            }

            const existing = this.productStockMap[pId].find(s => s.locationId === locId);

            existing
                ? existing.stockQty += qty : this.productStockMap[pId].push(stockLine);
        });

        console.log("Stock Map Ready:",this.productStockMap);
    },
 
    async handleComboProduct(
        values,
        order,
        configure = true,
        options = {}
    ) {

        const result = await super.handleComboProduct(
            values,
            order,
            configure,
            options
        );

        values.combo_line_ids?.forEach(([_, lineValues]) => {

            if (!lineValues?.combo_item_id) {
                return;
            }

            lineValues.custom_location_id =
                lineValues.combo_item_id.custom_location_id || false;

            console.log(
                "LOCATION INJECTED:",
                lineValues.combo_item_id.id,
                lineValues.custom_location_id
            );
        });

        console.log(
            "FINAL COMBO LINES:",
            values.combo_line_ids
        );

        return result;
    },
});