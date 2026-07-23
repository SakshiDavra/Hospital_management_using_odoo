/** @odoo-module **/

export class PricelistUtils {
    static isTimeSlotActive(pricelist, pos) {
        if (!pricelist?.enable_time_slot) return true;

        const now = pos?.getServerTime?.() || new Date();
        const currentTime = now.getHours() + now.getMinutes() / 60;
        const { time_slot_start: start, time_slot_end: end } = pricelist;
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const prevDay = new Date(today);
        prevDay.setDate(prevDay.getDate() - 1);
        const startDate = pricelist.schedule_start_date && new Date(pricelist.schedule_start_date);
        const endDate = pricelist.schedule_end_date && new Date(pricelist.schedule_end_date);
        const inSchedule = (date) => (!startDate || date >= startDate) && (!endDate || date <= endDate);
        return start <= end
            ? inSchedule(today) && currentTime >= start && currentTime <= end
            : currentTime >= start
                ? inSchedule(today)
                : inSchedule(prevDay);
    }
    static isPricelistValid(pricelist, pos) {
        return (
            pricelist && pricelist.state === "approved" && pricelist.is_available && this.isTimeSlotActive(pricelist, pos)
        );
    }
    static getEligiblePricelists(pos) {
        return pos.config.availablePricelists.filter(
            (pl) =>this.isPricelistValid(pl, pos) && !pl.manager_pin_required && pl.id !== pos.config.pricelist_id?.id);
    }
}