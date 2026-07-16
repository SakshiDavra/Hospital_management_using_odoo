/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { _t } from "@web/core/l10n/translation";
import { isPricelistValid } from "./pricelist_utils";

patch(ControlButtons.prototype, {
    getPricelistList() {
        const selectionList = this.pos.config.availablePricelists
            .filter((pricelist) => isPricelistValid(pricelist))
            .map((pricelist) => ({
                id: pricelist.id,
                label: pricelist.name,
                isSelected:
                    this.currentOrder.pricelist_id &&
                    pricelist.id === this.currentOrder.pricelist_id.id,
                item: pricelist,
            }));

        if (!this.pos.config.pricelist_id) {
            selectionList.push({
                id: null,
                label: _t("Default Price"),
                isSelected: !this.currentOrder.pricelist_id,
                item: null,
            });
        }
        return selectionList;
    },
});