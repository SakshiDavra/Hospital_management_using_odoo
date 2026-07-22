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
        const availablePricelists = this.config.availablePricelists;
        let rawPricelists;
        try {
            rawPricelists = (await this.data.silentCall("pos.session","load_data",
                    [[this.session.id], ["pos.preset", "product.pricelist"]]
                )
            )["product.pricelist"];
            console.log(rawPricelists);
        } catch (error) {
            console.error(error);
            return;
        }
        const newPricelistIds = [];
        for (const raw of rawPricelists) {
            let record = pricelistModel.get(raw.id);
            if (record) {
                record.update(raw);
            } else {
                record = pricelistModel.create(raw);
                newPricelistIds.push(record.id);
            }
            record.computeRuleIndexes?.();
            const index = availablePricelists.findIndex((p) => p.id === record.id);
            const isValid = PricelistUtils.isPricelistValid(record, this);
            if (isValid && index === -1) {
                availablePricelists.push(record);
            } else if (!isValid && index !== -1) {
                availablePricelists.splice(index, 1);
            }
        }
        if (!newPricelistIds.length) return;
        const rawItems = await this.data.call("product.pricelist", "get_new_pos_pricelist_items", [this.config.id, newPricelistIds]);
        const itemModel = this.models["product.pricelist.item"];
        for (const raw of rawItems) {
            itemModel.get(raw.id)?.update(raw) ?? itemModel.create(raw);
        }
        for (const id of newPricelistIds) {
            pricelistModel.get(id)?.computeRuleIndexes?.();
        }
    },

    getEligiblePricelists() {
        return this.config.availablePricelists.filter(
            (pl) => PricelistUtils.isPricelistValid(pl, this) && !pl.manager_pin_required && pl.id !== this.config.pricelist_id?.id
        );
    },

    getBestPricelistForOrder(order) {
        const eligible = this.getEligiblePricelists();
        if (!order || !eligible.length) {
            return order?.pricelist_id || null;
        }
        const original = order.pricelist_id;
        let best = original;
        try {
            order.setPricelist(original);
            let minTotal = order.priceIncl;
            for (const pricelist of eligible) {
                if (pricelist.id === original.id) continue;
                order.setPricelist(pricelist);
                const total = order.priceIncl;
                if (total < minTotal) {
                    minTotal = total;
                    best = pricelist;
                }
            }
            return best;
        } finally {
            order.setPricelist(original);
        }
    },

    recomputeBestPricelist(order) {
        if (!order || !order.lines.length) {
            return;
        }

        const best = this.getBestPricelistForOrder(order);
        if (best && order.pricelist_id?.id !== best.id) {
            order.setPricelist(best);
        }
    },

    addNewOrder() {
        const order = super.addNewOrder(...arguments);
        const pricelist = this.getEligiblePricelists()[0];
        if (pricelist) {
            order.setPricelist(pricelist);
        }
        return order;
    },

    async addLineToOrder(vals, order, opts = {}, configure = true) {
        const result = await super.addLineToOrder(...arguments);
        if (order) {
            this.recomputeBestPricelist(order);
        }
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
            await this.recomputeBestPricelist(order);
            return;
        }
        order.setPricelist(customerPricelist);
    },

    async orderDone(order) {
        await this.loadLatestPricelists();
        return super.orderDone(...arguments);
    },
});