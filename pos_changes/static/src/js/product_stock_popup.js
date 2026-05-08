/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class ProductStockPopup extends Component {
    static template = "pos_changes.ProductStockPopup";
    static components = { Dialog };
    static props = {
        title: { type: String },
        productName: { type: String },
        stockData: { type: Array },
        confirm: { type: Function },
        close: { type: Function },
    };

    setup() {

        this.state = useState({ selectedLocId: null });
    }

    async onAdd() {
        console.log("Selected Location ID in Popup:", this.state.selectedLocId); 
        if (!this.state.selectedLocId) {
            alert("Please select a location first!");
            return;
        }
        await this.props.confirm(this.state.selectedLocId);
    }
}