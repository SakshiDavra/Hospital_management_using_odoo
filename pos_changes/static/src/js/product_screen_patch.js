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
            return super.addProductToOrder(product);
        }

        const stockMap = this.pos.productStockMap || {};
        const stockInfo = stockMap[product.id] || [];

        const confirmed = await new Promise((resolve) => {
            this.dialog.add(ProductStockPopup, {
                title: _t("Confirm Selection"),
                productName: product.display_name,
                stockData: stockInfo,
                confirm: () => {
                    // ૧. પહેલા resolve true કરો
                    resolve(true);
                    // ૨. આ લાઈન પોપ-અપને બંધ કરી દેશે
                    this.dialog.closeAll(); 
                },
                close: () => {
                    resolve(false);
                    this.dialog.closeAll();
                }
            });
        });

        if (confirmed) {
            return super.addProductToOrder(product);
        }
    }
});