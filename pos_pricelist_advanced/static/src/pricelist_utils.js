/** @odoo-module **/

export class PricelistUtils {
    static isTimeSlotActive(pricelist, pos) {
        if (!pricelist || !pricelist.enable_time_slot) {
            return true;
        }

        const now = new Date();
        const currentTime = now.getHours() + now.getMinutes() / 60;
        const { time_slot_start: start, time_slot_end: end } = pricelist;
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const startDate = pricelist.schedule_start_date
            ? new Date(pricelist.schedule_start_date)
            : null;
        const endDate = pricelist.schedule_end_date
            ? new Date(pricelist.schedule_end_date)
            : null;
        const inSchedule = (date) => (!startDate || date >= startDate) && (!endDate || date <= endDate);
        if (start <= end) {
            return (inSchedule(today) && currentTime >= start && currentTime <= end);
        }
        if (currentTime <= end) {
            if (endDate && today > endDate) {
                return false;
            }
            const prevDay = new Date(today);
            prevDay.setDate(prevDay.getDate() - 1);
            return inSchedule(prevDay);
        }
        return currentTime >= start && inSchedule(today);
    }

    static isPricelistValid(pricelist, pos) {
        return (
            pricelist && pricelist.state === "approved" && pricelist.is_available && this.isTimeSlotActive(pricelist, pos)
        );
    }
}