/** @odoo-module **/
/* global Sha1 */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { CashierSelectionPopup } from "@pos_hr/app/components/popups/cashier_selection_popup/cashier_selection_popup";
import { NumberPopup } from "@point_of_sale/app/components/popups/number_popup/number_popup";
import { makeAwaitable, ask } from "@point_of_sale/app/utils/make_awaitable_dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { PricelistUtils } from "../../pricelist_utils";
patch(PosStore.prototype, {
    getServerTime() {
        return new Date(Date.now() + (this.serverTimeOffset || 0));
    },
    async loadLatestPricelists() {
        const pricelistModel = this.models["product.pricelist"];
        const itemModel = this.models["product.pricelist.item"];
        const availablePricelists = this.config.availablePricelists;
        let data;
        try {
            data = await this.data.silentCall("pos.config","get_new_pricelists",[this.config.id, pricelistModel.map((p) => p.id)]);
        } catch (error) {
            console.error(error);
            return;
        }
        const { pricelists = [], items = [] } = data;
        if (!pricelists.length) return;
        const updatedPricelists = [];
        for (const raw of pricelists) {
            let record = pricelistModel.get(raw.id);
            if (record) {
                record.update(raw);
            } else {
                record = pricelistModel.create(raw);
            }
            updatedPricelists.push(record);
            const index = availablePricelists.findIndex((p) => p.id === record.id);
            const isValid = PricelistUtils.isPricelistValid(record, this);
            if (isValid && index === -1) {
                availablePricelists.push(record);
            } else if (!isValid && index !== -1) {
                availablePricelists.splice(index, 1);
            }
        }
        for (const raw of items) {
            itemModel.get(raw.id)?.update(raw) ?? itemModel.create(raw);
        }
        for (const pricelist of updatedPricelists) {
            pricelist.computeRuleIndexes?.();
        }
    },
    getBestPricelistForOrder(order) {
        if (!order) return null;
        const eligible = PricelistUtils.getEligiblePricelists(this);
        if (!eligible.length) return order.pricelist_id;
        const original = order.pricelist_id;
        let best = original;
        try {
            order.setPricelist(original);
            let minTotal = order.priceIncl;
            for (const pricelist of eligible) {
                if (pricelist.id === original.id) continue;
                order.setPricelist(pricelist);
                if (order.priceIncl < minTotal) {
                    minTotal = order.priceIncl;
                    best = pricelist;
                }
            }
            return best;
        } finally {
            order.setPricelist(original);
        }
    },
    recomputeBestPricelist(order) {
        if (!order) return;
        if (!order.lines.length) {
            const pricelist = PricelistUtils.getEligiblePricelists(this)[0];
            if (pricelist && pricelist.id !== order.pricelist_id?.id) {
                order.setPricelist(pricelist);
            }
            return;
        }
        const best = this.getBestPricelistForOrder(order);
        if (best?.id !== order.pricelist_id?.id) {
            order.setPricelist(best);
        }
    },
    addNewOrder() {
        const order = super.addNewOrder(...arguments);
        const pricelist = PricelistUtils.getEligiblePricelists(this)[0];
        pricelist && order.setPricelist(pricelist);
        return order;
    },
    async addLineToOrder(vals, order, opts = {}, configure = true) {
        const result = await super.addLineToOrder(...arguments);
        if (order) this.recomputeBestPricelist(order);
        return result;
    },
    async verifyManagerPinForPricelist(pricelist, partnerName) {
        if (!pricelist.manager_pin_required) return true;
        const apply = await ask(this.dialog, {
            title: _t("Apply Customer Pricelist?"),
            body: _t("%s has a pricelist that requires manager approval. Apply it to this order?", partnerName),
        });
        if (!apply) return false;
        const approvers = (this.config.advanced_employee_ids || []).filter((employee) => employee._pin);
        if (!approvers.length) {
            this.dialog.add(AlertDialog, {
                title: _t("Access Denied"),
                body: _t("No authorized employee with a configured PIN was found."),
            });
            return false;
        }
        const selectedManager = approvers.length === 1
            ? approvers[0] : await makeAwaitable(this.dialog, CashierSelectionPopup, { employees: approvers });
                if (!selectedManager) return false;
        const enteredPin = await makeAwaitable(this.dialog, NumberPopup, {
            title: _t("Manager PIN"),
            formatDisplayedValue: (x) => x.replace(/./g, "•"),
        });
                if (!enteredPin) return false;

        if (Sha1.hash(enteredPin) !== selectedManager._pin) {
            this.dialog.add(AlertDialog, {
                title: _t("Incorrect PIN"),
                body: _t("The PIN you entered is incorrect."),
            });
            return false;
        }
        return true;
    },
    async setPartnerToCurrentOrder(partner) {
        const order = this.getOrder();
        super.setPartnerToCurrentOrder(...arguments);
        if (!order) return;
        const customerPricelist = order.pricelist_id;
        let shouldRecompute = !partner || !customerPricelist || !PricelistUtils.isPricelistValid(customerPricelist, this);
        if (!shouldRecompute) {
            const allowed = await this.verifyManagerPinForPricelist(customerPricelist, partner.name);
            shouldRecompute = !allowed;
        }
        if (shouldRecompute) {
            this.recomputeBestPricelist(order);
            return;
        }
        order.setPricelist(customerPricelist);
    },
    async orderDone(order) {
        await this.loadLatestPricelists();
        return super.orderDone(...arguments);
    },
});