/** @odoo-module **/

import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class ConsultationTimer extends Component {

    setup() {
        this.state = useState({ timer: "00:00:00" });
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
        this.interval = setInterval(() => {

            if (!this.props || !this.props.record || !this.props.record.data) {
                return;
            }

            const record = this.props.record.data;

            if (record.consultation_start && !record.consultation_end) {

                const start = new Date(record.consultation_start);
                const now = new Date();

                let diff = Math.floor((now - start) / 1000);

                let h = Math.floor(diff / 3600);
                let m = Math.floor((diff % 3600) / 60);
                let s = diff % 60;

                this.state.timer =
                    `${String(h).padStart(2,'0')}:` +
                    `${String(m).padStart(2,'0')}:` +
                    `${String(s).padStart(2,'0')}`;
            }

        }, 1000);
    }
}


ConsultationTimer.template = "hospital_management.ConsultationTimer";

registry.category("view_widgets").add("consultation_timer", ConsultationTimer);