/** @odoo-module **/

import { ProductConfiguratorPopup } from "@point_of_sale/app/components/popups/product_configurator_popup/product_configurator_popup";
import { patch } from "@web/core/utils/patch";
import { ProductStockPopup } from "@pos_changes/js/product_stock_popup";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

patch(ProductConfiguratorPopup.prototype, {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
    },

    async confirm() {

        // Variant product
        let selectedProduct = this.product;

        // Configurable only product
        if (!selectedProduct) {

            if (this.props.productTemplate.product_variant_ids.length) {
                selectedProduct =
                    this.props.productTemplate.product_variant_ids[0];
            }
        }

        console.log("Selected Product:", selectedProduct);

        if (!selectedProduct) {
            return super.confirm();
        }

        const stockMap = this.pos.productStockMap || {};
        const stockInfo = stockMap[selectedProduct.id] || [];

        console.log("Stock Info:", stockInfo);

        let selectedLocationId = null;

        // Multiple locations
        if (stockInfo.length > 1) {

            selectedLocationId = await new Promise((resolve) => {
                this.dialog.add(ProductStockPopup, {
                    title: _t("Select Location"),
                    productName: selectedProduct.display_name,
                    stockData: stockInfo,
                    confirm: (locId) => resolve(locId),
                    close: () => resolve(false),
                });
            });

            if (!selectedLocationId) {
                return;
            }

        }

        // Single location
        else if (stockInfo.length === 1) {
            selectedLocationId = stockInfo[0].locationId;
        }

        const payload = this.computePayload();

        payload.product_id = selectedProduct.id;

        if (selectedLocationId) {
            payload.extras = {
                custom_location_id: selectedLocationId,
            };
        }

        console.log("FINAL PAYLOAD:", payload);
        this.props.getPayload(payload);
        await new Promise((resolve) => setTimeout(resolve, 0));
        const order = this.pos.getOrder();
        const lastLine = order.lines[order.lines.length - 1];

        if (lastLine && selectedLocationId) {

            lastLine.custom_location_id = selectedLocationId;

            console.log(
                "Configurable Product Location Updated:",
                lastLine.custom_location_id
            );
        }

        this.props.close();
        this.dialog.closeAll();
    },
});