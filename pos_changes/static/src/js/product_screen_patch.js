/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { ProductStockPopup } from "@pos_changes/js/product_stock_popup";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

patch(ProductScreen.prototype, {

    setup() {
        super.setup();
        this.dialog = useService("dialog");
    },

    async addProductToOrder(product) {

        // CONFIGURABLE PRODUCT
        if (product.isConfigurable()) {
            return await super.addProductToOrder(product);
        }

        // COMBO PRODUCT
        if (product.combo_ids?.length) {
            return await super.addProductToOrder(product);
        }

        const stockMap = this.pos.productStockMap || {};
        const variantId = product.product_variant_id?.id ||
                          product.product_variant_ids?.[0]?.id ||
                          product.id;

        const stockInfo = stockMap[variantId] || [];
        console.log( "STOCK INFO:", stockInfo );

        // POSITIVE STOCK ONLY
        const availableStockInfo = stockInfo.filter((loc) => loc.stockQty > 0);

        console.log( "AVAILABLE STOCK:",availableStockInfo );

        let selectedLocationId = null;

        // NO STOCK
        if (!availableStockInfo.length) {
            alert( product.display_name + " is not available!" );
            return;
        }

        // ONLY ONE POSITIVE LOCATION
        // AUTO SELECT
        if (availableStockInfo.length === 1) {
            selectedLocationId = availableStockInfo[0].locationId;
            console.log("AUTO SELECTED LOCATION:", selectedLocationId);
        }

        // MULTIPLE POSITIVE LOCATIONS
        else {
            selectedLocationId = await new Promise((resolve) => {

                    this.dialog.add(
                        ProductStockPopup,
                        {
                            title: _t("Select Location"),
                            productName: product.display_name,
                            stockData: availableStockInfo,

                            confirm: (locId) => {
                                resolve(locId);
                                this.dialog.closeAll();
                            },

                            close: () => {
                                resolve(false);
                                this.dialog.closeAll();
                            },
                        }
                    );
                });

            if (!selectedLocationId) {
                return;
            }
        }

        const options = selectedLocationId
                ? {
                    extras: {
                        custom_location_id:
                            selectedLocationId,
                    },
                }
                : {};

        const result = await super.addProductToOrder(product, options);
        const order = this.pos.getOrder();
        const lastLine = order.lines[order.lines.length - 1];

        if (lastLine && selectedLocationId) {
            lastLine.custom_location_id = selectedLocationId;
            console.log("LOCATION SAVED:", selectedLocationId);
        }
        return result;
    },
});