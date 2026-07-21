/** @odoo-module **/

export function isTimeSlotActive(pricelist, pos) {
    if (!pricelist || !pricelist.enable_time_slot) {
        return true;
    }
    const now = pos && typeof pos.getServerTime === "function" ? pos.getServerTime() : new Date();
    const currentTime = now.getHours() + now.getMinutes() / 60;
    return currentTime >= pricelist.time_slot_start && currentTime <= pricelist.time_slot_end;
}

export function isPricelistValid(pricelist, pos) {
    return Boolean(pricelist && pricelist.state === "approved" && pricelist.is_available &&
        isTimeSlotActive(pricelist, pos)
    );
}