/** @odoo-module **/

import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";

export class ClearButton extends Component {
    static template = "pos_changes.ClearButton";
    static props = {}; 

    setup() {
        this.pos = usePos();
    }

    onClick() {
        const order = this.pos.getOrder();

        if (!order) return;

        const selectedLine = order.getSelectedOrderline();

        if (selectedLine) {
            order.removeOrderline(selectedLine);
        } else {
            alert("Please select item first");
        }
    }
}

ControlButtons.components = {
    ...ControlButtons.components,
    ClearButton,
};