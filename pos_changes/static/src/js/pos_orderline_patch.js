/** @odoo-module **/

import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";

import { patch } from "@web/core/utils/patch";

patch(PosOrderline.prototype, {

    setup(vals) {
        super.setup(vals);

        this.custom_location_id =
            vals.custom_location_id || false;
    },

    serializeForORM(opts = {}) {

        const data =
            super.serializeForORM(opts);

        data.custom_location_id =
            this.custom_location_id?.id ||
            this.custom_location_id ||
            false;

        console.log(
            "SERIALIZED:",
            data.custom_location_id
        );

        return data;
    },
});