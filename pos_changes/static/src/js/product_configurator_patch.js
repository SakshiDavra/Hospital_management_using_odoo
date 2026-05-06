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
        // 1. Variant product find karo
        const selectedProduct = this.product || this.props.productTemplate;
        
        if (!selectedProduct) {
            return super.confirm();
        }

        const stockMap = this.pos.productStockMap || {};
        const stockInfo = stockMap[selectedProduct.id] || [];

        // 2. Stock Popup open karo
        const confirmed = await new Promise((resolve) => {
            this.dialog.add(ProductStockPopup, {
                title: _t("Confirm Selection"),
                productName: selectedProduct.display_name,
                stockData: stockInfo,
                confirm: () => {
                    resolve(true);
                },
                close: () => {
                    resolve(false);
                }
            });
        });

        // 3. Jo user 'Add to Order' dabe to:
        if (confirmed) {
            // Payload calculate kari lo (Variants na price extra calculation sathe)
            const payload = this.computePayload();
            
            // Order line ma product add karo
            this.props.getPayload(payload);
            
            // Have Configurator popup bandh karo
            this.props.close();
            
            // Location popup ne bandh karva mate safe side closeAll call kari shako
            this.dialog.closeAll();
        }
    }
});