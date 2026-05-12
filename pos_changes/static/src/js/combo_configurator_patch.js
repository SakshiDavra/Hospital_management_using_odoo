/** @odoo-module **/

import { ComboConfiguratorPopup } from "@point_of_sale/app/components/popups/combo_configurator_popup/combo_configurator_popup";
import { patch } from "@web/core/utils/patch";
import { ProductStockPopup } from "@pos_changes/js/product_stock_popup";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

patch(ComboConfiguratorPopup.prototype, {

    setup() {
        super.setup();
        this.dialog = useService("dialog");
        this.state.customLocations = {};
    },

    async onClickProduct(product, combo_item) {

        const stockInfo = this.pos.productStockMap?.[product.id] || [];
        console.log("Combo Product Stock:",stockInfo);

        // ONLY POSITIVE STOCK
        const availableStockInfo = stockInfo.filter((loc) => loc.stockQty > 0);
        let selectedLocationId = false;

        // NO STOCK
        if (!availableStockInfo.length) {
            alert(product.display_name + " is not available!");
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

            selectedLocationId =
                await new Promise((resolve) => {
                    this.dialog.add(
                        ProductStockPopup,
                        {
                            title: _t( "Select Location for " ) + product.display_name,
                            productName: product.display_name,
                            stockData: availableStockInfo,
                            confirm: (locId) => {resolve(locId);},
                            close: () => {resolve(false);},
                        }
                    );
                });

            if (!selectedLocationId) {
                return;
            }
        }

        // SAVE LOCATION
        this.state.customLocations[ combo_item.id] = selectedLocationId;
        console.log("LOCATION SAVED:",combo_item.id,selectedLocationId);
        const combo = combo_item.combo_id;

        // CONFIGURABLE PRODUCT
        if (
            product.product_tmpl_id &&
            product.product_tmpl_id.needToConfigure()
        ) {

            return this.onClickConfigurableProduct(product,combo_item,combo);
        }

        // SIMPLE PRODUCT
        return this.onClickSimpleProduct(combo_item, combo);
    },

    getSelectedComboItems() {

        const itemsIncluded = [];
        const itemsExtra = [];
        const tracker = {};

        Object.values(this.state.qty).forEach(
            (comboItems) => {

                Object.entries(comboItems)
                    .filter(
                        ([, qty]) => qty > 0
                    )
                    .forEach(
                        ([itemId, qty]) => {
                            const comboItem = this.pos.models["product.combo.item"].get(itemId);
                            const locationId = this.state.customLocations[comboItem.id] || false;

                            // SAVE LOCATION
                            comboItem.custom_location_id = locationId;
                            const comboId = comboItem.combo_id.id;
                            const freeQty = comboItem.combo_id.qty_free;
                            tracker[comboId] = tracker[comboId] || 0;
                            const remaining = freeQty - tracker[comboId];
                            const config = this.state.configuration[ comboItem.id];

                            // INCLUDED ITEMS
                            if (remaining > 0) {
                                const includedQty = Math.min(qty, remaining);
                                itemsIncluded.push({
                                    combo_item_id: comboItem,
                                    configuration:config,
                                    qty: includedQty,
                                    custom_location_id: locationId,
                                });

                                tracker[comboId] += includedQty;
                                qty -= includedQty;
                            }

                            // EXTRA ITEMS
                            if (qty > 0) {
                                itemsExtra.push({
                                    combo_item_id: comboItem,
                                    configuration: config,
                                    qty: qty,
                                    custom_location_id: locationId,
                                });
                            }
                        }
                    );
            }
        );

        console.log("FINAL COMBO PAYLOAD:",itemsIncluded,itemsExtra);
        return [itemsIncluded,itemsExtra,];
    },
});