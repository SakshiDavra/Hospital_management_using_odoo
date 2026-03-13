/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { CalendarController } from "@web/views/calendar/calendar_controller";

class HospitalCalendarController extends CalendarController {

    async createRecord() {
        const result = await super.createRecord(...arguments);
        await this.model.load();
        return result;
    }
}

const hospitalCalendarView = {
    ...calendarView,
    Controller: HospitalCalendarController,
};

registry.category("views").add("hospital_calendar", hospitalCalendarView);