/** @odoo-module **/
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class ProductStockPopup extends Component {
    static template = "pos_changes.ProductStockPopup";
    static components = { Dialog };
    static props = {
        title: { type: String },
        productName: { type: String },
        stockData: { type: Array },
        confirm: { type: Function },
        close: { type: Function }, // આ Dialog દ્વારા ઓટોમેટિક મળે છે
    };

    async onAdd() {
        await this.props.confirm();
        this.props.close();
    }
}