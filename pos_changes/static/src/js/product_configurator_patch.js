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

        let selectedProduct = this.product;

        // CONFIGURABLE ONLY PRODUCT
        if (!selectedProduct) {

            if(
                this.props.productTemplate.product_variant_ids.length) {
                selectedProduct = this.props.productTemplate.product_variant_ids[0];}
        }

        if (!selectedProduct) {
            return super.confirm();
        }

        const stockMap = this.pos.productStockMap || {};
        const stockInfo = stockMap[selectedProduct.id] || [];

        console.log( "CONFIG PRODUCT STOCK:", stockInfo );

        // POSITIVE STOCK ONLY
        const availableStockInfo = stockInfo.filter((loc) => loc.stockQty > 0 );
        console.log("AVAILABLE STOCK:", availableStockInfo);

        let selectedLocationId = null;

        // NO STOCK
        if (!availableStockInfo.length) {
            alert(selectedProduct.display_name + " is not available!");
            return;
        }

        // ONLY ONE POSITIVE LOCATION
        // AUTO SELECT
        if (availableStockInfo.length === 1) {
            selectedLocationId = availableStockInfo[0].locationId;
            console.log("AUTO SELECTED LOCATION:", selectedLocationId );
        }

        // MULTIPLE POSITIVE LOCATIONS
        else {
            selectedLocationId =
                await new Promise((resolve) => {

                    this.dialog.add(
                        ProductStockPopup,
                        {
                            title: _t("Select Location"),
                            productName:selectedProduct.display_name,
                            stockData:availableStockInfo,
                            confirm: (locId) => resolve(locId),
                            close: () =>  resolve(false),
                        }
                    );
                });

            if (!selectedLocationId) {
                return;
            }
        }

        const payload = this.computePayload();
        payload.product_id = selectedProduct.id;

        // SAVE LOCATION
        if (selectedLocationId) {
            payload.extras = {custom_location_id: selectedLocationId,};
        }

        console.log("FINAL PAYLOAD:",payload);
        this.props.getPayload( payload );
        await new Promise((resolve) => setTimeout(resolve, 0));
        const order =this.pos.getOrder();
        const lastLine = order.lines[ order.lines.length - 1 ];

        if (
            lastLine &&
            selectedLocationId
        ) {

            lastLine.custom_location_id = selectedLocationId;

            console.log(
                "LOCATION SAVED:", selectedLocationId
            );
        }
        // CLOSE ALL POPUPS
        this.dialog.closeAll();

        return;
    },
});