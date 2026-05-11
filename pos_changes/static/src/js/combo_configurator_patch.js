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

        let selectedLocationId = false;

        // MULTIPLE LOCATION
        if (stockInfo.length > 1) {

            selectedLocationId = await new Promise((resolve) => {

                this.dialog.add(ProductStockPopup, {

                    title:
                        _t("Select Location for ") +
                        product.display_name,

                    productName:
                        product.display_name,

                    stockData: stockInfo,

                    confirm: (locId) => {
                        resolve(locId);
                    },

                    close: () => {
                        resolve(false);
                    },
                });
            });

            if (!selectedLocationId) {
                return;
            }

        } else if (stockInfo.length === 1) {

            selectedLocationId = stockInfo[0].locationId;
        }

        // SAVE LOCATION
        this.state.customLocations[combo_item.id] = selectedLocationId;

        console.log(
            "LOCATION SAVED:",
            combo_item.id,
            selectedLocationId
        );

        // ORIGINAL FLOW
        const combo = combo_item.combo_id;

        if (product.product_tmpl_id.needToConfigure()) {

            return this.onClickConfigurableProduct(
                product,
                combo_item,
                combo
            );
        }

        return this.onClickSimpleProduct(
            combo_item,
            combo
        );
    },

    getSelectedComboItems() {

        const itemsIncluded = [];
        const itemsExtra = [];

        const tracker = {};

        Object.values(this.state.qty).forEach(
            (comboItems) => {

                Object.entries(comboItems)
                    .filter(([, qty]) => qty > 0)
                    .forEach(([itemId, qty]) => {
                        const comboItem = this.pos.models["product.combo.item"].get(itemId);
                        const locationId = this.state.customLocations[comboItem.id] || false;

                        // IMPORTANT
                        comboItem.custom_location_id = locationId;
                        const comboId = comboItem.combo_id.id;
                        const freeQty = comboItem.combo_id.qty_free;
                        tracker[comboId] = tracker[comboId] || 0;
                        const remaining = freeQty - tracker[comboId];
                        const config = this.state.configuration[comboItem.id];

                        if (remaining > 0) {

                            const includedQty =
                                Math.min(
                                    qty,
                                    remaining
                                );

                            itemsIncluded.push({
                                combo_item_id: comboItem,
                                configuration: config,
                                qty: includedQty,
                                custom_location_id: locationId,
                            });

                            tracker[comboId] +=includedQty;
                            qty -= includedQty;
                        }
                        if (qty > 0) {

                            itemsExtra.push({
                                combo_item_id:comboItem,
                                configuration:config,
                                qty,
                                custom_location_id:locationId,
                            });
                        }
                    });
            }
        );

        console.log(
            "FINAL COMBO PAYLOAD:",
            itemsIncluded,
            itemsExtra
        );

        return [
            itemsIncluded,
            itemsExtra,
        ];
    },
});
