/** @odoo-module **/

export function isScheduleActive(pricelist) {
    if (!pricelist || !pricelist.enable_schedule) {
        return true;
    }

    if (pricelist.recurrency && ['yearly', 'monthly'].includes(pricelist.rrule_type)) {
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
}

export function isTimeSlotActive(pricelist) {
    if (!pricelist || !pricelist.enable_time_slot) {
        return true;
    }
    const now = new Date();
    const currentTime = now.getHours() + now.getMinutes() / 60;
    return (currentTime >= pricelist.time_slot_start && currentTime <= pricelist.time_slot_end);
}

export function isPricelistValid(pricelist) {
    if (!pricelist) return false;
    
    return (pricelist.state === "approved" && isScheduleActive(pricelist) && isTimeSlotActive(pricelist) &&  pricelist.is_available);
}