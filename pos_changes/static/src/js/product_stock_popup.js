
/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class ProductStockPopup extends Component {

    static template = "pos_changes.ProductStockPopup";
    static components = {
        Dialog,
    };

    static props = {
        title: { type: String },
        productName: { type: String },
        stockData: { type: Array },
        confirm: { type: Function },
        close: { type: Function },
    };

    setup() {

        this.state = useState({selectedLocId: null,});
    }

    async onAdd() {

        if (!this.state.selectedLocId) {
            alert("Please select a location first!");
            return;
        }
        const selectedLocation = this.props.stockData.find(
                loc => loc.locationId === this.state.selectedLocId
            );

        // OUT OF STOCK
        if (
            !selectedLocation ||
            selectedLocation.stockQty <= 0
        ) {
            alert("Product is not available in this location!");
            return;
        }

        await this.props.confirm(this.state.selectedLocId);
        this.props.close();
    }
    onClose() {
        this.props.close();
    }
}
