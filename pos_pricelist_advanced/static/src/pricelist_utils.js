/** @odoo-module **/

export function isTimeSlotActive(pricelist, pos) {
    if (!pricelist || !pricelist.enable_time_slot) return true;

    const now = pos?.getServerTime?.() || new Date();
    const currentTime = now.getHours() + now.getMinutes() / 60;
    const start = pricelist.time_slot_start;
    const end = pricelist.time_slot_end;
    if (start < end) {
        return currentTime >= start && currentTime <= end;
    }
    return currentTime >= start || currentTime <= end;
}

export function isPricelistValid(pricelist, pos) {
    return (pricelist && pricelist.state === "approved" && pricelist.is_available && isTimeSlotActive(pricelist, pos));
}