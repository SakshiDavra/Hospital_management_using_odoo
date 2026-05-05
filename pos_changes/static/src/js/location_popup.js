import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class LocationPopup extends Component {
    static template = "pos_location_selector.LocationPopup";
    static components = { Dialog };

    static props = {
        locations: Array,
        close: Function,
    };

    setup() {
        this.state = useState({
            selected: null,
        });
    }

    selectLocation(loc) {
        this.state.selected = loc;
    }

    confirm() {
        this.props.close({
            confirmed: true,
            location: this.state.selected,
        });
    }

    cancel() {
        this.props.close({ confirmed: false });
    }
}