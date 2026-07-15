/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { _t } from "@web/core/l10n/translation";

patch(ControlButtons.prototype, {
    isScheduleActive(pricelist) {
        if (!pricelist.enable_schedule) {
            return true;
        }
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        if (pricelist.schedule_start_date) {
            const start = new Date(pricelist.schedule_start_date);
            start.setHours(0, 0, 0, 0);
            if (today < start) {
                return false;
            }
        }
        if (pricelist.schedule_end_date) {
            const end = new Date(pricelist.schedule_end_date);
            end.setHours(0, 0, 0, 0);
            if (today > end) {
                return false;
            }
        }
        return true;
    },

    isTimeSlotActive(pricelist) {
        if (!pricelist.enable_time_slot) {
            return true;
        }
        const now = new Date();
        const currentTime = now.getHours() + now.getMinutes() / 60;
        return (
            currentTime >= pricelist.time_slot_start &&
            currentTime <= pricelist.time_slot_end
        );
    },

    isRecurrenceActive(pricelist) {
        if (!pricelist.recurrency) {
            return true;
        }
        const today = new Date();
        if (pricelist.until) {
            const until = new Date(pricelist.until);
            until.setHours(0, 0, 0, 0);
            const current = new Date(today);
            current.setHours(0, 0, 0, 0);
            if (current > until) {
                return false;
            }
        }

        switch (pricelist.rrule_type) {
            case "daily":
                return true;
            case "weekly": {
                const day = today.getDay();
                return (
                    (day === 0 && pricelist.sun) ||
                    (day === 1 && pricelist.mon) ||
                    (day === 2 && pricelist.tue) ||
                    (day === 3 && pricelist.wed) ||
                    (day === 4 && pricelist.thu) ||
                    (day === 5 && pricelist.fri) ||
                    (day === 6 && pricelist.sat)
                );
            }

            case "monthly":
                if (pricelist.month_by === "date") {
                    return today.getDate() === pricelist.day;
                }
                return true;
            case "yearly":
                if (pricelist.month_by === "date") {
                    return today.getDate() === pricelist.day;
                }
                return true;
            default:
                return true;
        }
    },

    getPricelistList() {
        const selectionList = this.pos.config.availablePricelists
            .filter(
                (pricelist) =>
                    pricelist.state === "approved" &&
                    this.isScheduleActive(pricelist) &&
                    this.isTimeSlotActive(pricelist) &&
                    this.isRecurrenceActive(pricelist)
            )
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