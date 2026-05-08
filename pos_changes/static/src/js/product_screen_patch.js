// /** @odoo-module **/
// import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
// import { patch } from "@web/core/utils/patch";
// import { ProductStockPopup } from "@pos_changes/js/product_stock_popup";
// import { useService } from "@web/core/utils/hooks";
// import { _t } from "@web/core/l10n/translation";

// patch(ProductScreen.prototype, {
//     setup() {
//         super.setup();
//         this.dialog = useService("dialog");
//     },

//     async addProductToOrder(product) {
//         // ૧. સ્ટોક મેપમાંથી ડેટા મેળવો
//         const stockMap = this.pos.productStockMap || {};
//         const stockInfo = stockMap[product.id] || stockMap[product.product_variant_ids?.[0]?.id] || [];

//         let selectedLocationId = null;

//         // ૨. લોકેશન સિલેક્શન લોજિક
//         if (stockInfo.length > 1) {
//             selectedLocationId = await new Promise((resolve) => {
//                 this.dialog.add(ProductStockPopup, {
//                     title: _t("Multiple Locations Found"),
//                     productName: product.display_name,
//                     stockData: stockInfo,
//                     confirm: (locId) => {
//                         resolve(locId);
//                         this.dialog.closeAll(); 
//                     },
//                     close: () => {
//                         resolve(false);
//                         this.dialog.closeAll();
//                     }
//                 });
//             });
//             if (!selectedLocationId) return;
//         } else if (stockInfo.length === 1) {
//             selectedLocationId = stockInfo[0].locationId;
//         }

//         const options = selectedLocationId ? { extras: { custom_location_id: selectedLocationId } } : {};
//         const result = await super.addProductToOrder(product, options);
//         const order = this.pos.getOrder();
//         const lastLine = order.lines[order.lines.length - 1];

//         if (lastLine && selectedLocationId) {
//             // આ રીતે ડેટા સેટ કરવાથી Odoo તેને ઓટોમેટિકલી સિંક લિસ્ટમાં લેશે
//             lastLine.update({ custom_location_id: selectedLocationId });
//             console.log("Data Assigned via Update:", lastLine.custom_location_id);
//         }
//         return result;
//     }
// });

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
        if (product.isConfigurable()) {
            return await super.addProductToOrder(product);
        }

        const stockMap = this.pos.productStockMap || {};
        const stockInfo = stockMap[product.id] || [];

        let selectedLocationId = null;

        if (stockInfo.length > 1) {
            selectedLocationId = await new Promise((resolve) => {
                this.dialog.add(ProductStockPopup, {
                    title: _t("Select Location"),
                    productName: product.display_name,
                    stockData: stockInfo,
                    confirm: (locId) => {
                        resolve(locId);
                        this.dialog.closeAll();
                    },
                    close: () => {
                        resolve(false);
                        this.dialog.closeAll();
                    },
                });
            });

            if (!selectedLocationId) return;

        } else if (stockInfo.length === 1) {
            selectedLocationId = stockInfo[0].locationId;
        }

        const options = selectedLocationId
            ? {
                extras: {
                    custom_location_id: selectedLocationId,
                },
            }
            : {};

        const result = await super.addProductToOrder(product, options);

        const order = this.pos.getOrder();
        const lastLine = order.lines[order.lines.length - 1];

        if (lastLine && selectedLocationId) {
            lastLine.update({
                custom_location_id: selectedLocationId,
            });

            console.log(
                "Simple Product Location:",
                selectedLocationId
            );
        }

        return result;
    },
});