/* @odoo-module */

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { deserializeDateTime } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";

export class ProcessingTimer extends Component {
    setup() {
        this.state = useState({ time: "00:00:00" });
        this.interval = null;

        onMounted(() => {
            this.startTimer();
        });

        onWillUnmount(() => {
            if (this.interval) {
                clearInterval(this.interval);
            }
        });
    }

    startTimer() {
        const record = this.props.record;
        const startTimeStr = record && record.data.processing_start_time;

        if (!startTimeStr) return;

        const start = typeof startTimeStr === 'string'
            ? deserializeDateTime(startTimeStr)
            : startTimeStr;

        this.interval = setInterval(() => {
            const now = luxon.DateTime.now();
            const diff = now.diff(start, ['hours', 'minutes', 'seconds']);

            if (diff.as('seconds') < 0) {
                this.state.time = "00:00:00";
                return;
            }

            const hrs = String(Math.floor(diff.hours)).padStart(2, "0");
            const mins = String(Math.floor(diff.minutes)).padStart(2, "0");
            const secs = String(Math.floor(diff.seconds)).padStart(2, "0");

            this.state.time = `${hrs}:${mins}:${secs}`;
        }, 1000);
    }
}

ProcessingTimer.template = "hospital.ProcessingTimer";
ProcessingTimer.props = ["*"];

registry.category("view_widgets").add("processing_timer", {
    component: ProcessingTimer,
});