/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { SelectionPopup } from "@point_of_sale/app/components/popups/selection_popup/selection_popup";
import { makeAwaitable } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { _t } from "@web/core/l10n/translation";
import { isPricelistValid } from "./pricelist_utils";

patch(ControlButtons.prototype, {
    getPricelistList() {
        const selectionList = this.pos.config.availablePricelists
            .filter((pricelist) => isPricelistValid(pricelist, this.pos))
            .map((pricelist) => ({
                id: pricelist.id,
                label: pricelist.name,
                isSelected: this.currentOrder.pricelist_id && pricelist.id === this.currentOrder.pricelist_id.id,
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

    async clickPricelist() {
        const pricelist = await makeAwaitable(this.dialog, SelectionPopup, {
            title: _t("Select Pricelist"),
            list: this.getPricelistList(),
        });
        if (!pricelist) return;
        const pinVerified = await this.pos.verifyManagerPinForPricelist(pricelist);
        if (pinVerified) {
            this.pos.selectPricelist(pricelist);
        }
    },
});