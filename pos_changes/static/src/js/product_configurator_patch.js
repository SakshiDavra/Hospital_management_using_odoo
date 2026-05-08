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
        const selectedProduct = this.product || this.props.productTemplate;
        if (!selectedProduct) return super.confirm();

        const stockMap = this.pos.productStockMap || {};
        const stockInfo = stockMap[selectedProduct.id] || [];

        let selectedLocationId = null;

        if (stockInfo.length > 1) {
            selectedLocationId = await new Promise((resolve) => {
                this.dialog.add(ProductStockPopup, {
                    title: _t("Confirm Selection"),
                    productName: selectedProduct.display_name,
                    stockData: stockInfo,
                    confirm: (locId) => resolve(locId),
                    close: () => resolve(false)
                });
            });
            if (!selectedLocationId) return;

        } else if (stockInfo.length === 1) {
            selectedLocationId = stockInfo[0].locationId;
        }

        const payload = this.computePayload();
        
        if (selectedLocationId) {
            payload.custom_location_id = selectedLocationId;
            console.log("Configurator: Adding Location ID to payload:", selectedLocationId);
        }

        this.props.getPayload(payload);
        this.props.close();
        this.dialog.closeAll();
    }
});