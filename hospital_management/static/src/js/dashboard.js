/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

import { Layout } from "@web/search/layout";
import { CounterCard } from "./components/counter_card";

export class HospitalDashboard extends Component {

    static components = { Layout, CounterCard };

    setup() {
        this.action = useService("action");

        this.state = useState({
            cards: [
                { title: "Total Patients", key: "patients", bg: "bg-primary-subtle text-primary", action: "patient" },
                { title: "Total Doctors", key: "doctors", bg: "bg-success-subtle text-success", action: "doctor" },
                { title: "Total Appointments", key: "appointments", bg: "bg-warning-subtle text-warning", action: "appointment" },

                { title: "Today's Appointments", key: "today_appointments", bg: "bg-info-subtle text-info", action: "today" },

                { title: "Next Week Appointments", key: "week_appointments", bg: "bg-secondary-subtle text-secondary", action: "week" },
                { title: "Past Week Appointments", key: "past_week", bg: "bg-danger-subtle text-danger", action: "past_week" },
            ],
            data: {
                patients: 0,
                doctors: 0,
                appointments: 0,
            },
        });

        onWillStart(async () => {
            const res = await rpc("/hospital/dashboard/data");
            this.state.data = res;
        });
    }

    openList(type) {

        if (type === "today") {
            const today = new Date().toISOString().split('T')[0];

            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Today's Appointments",
                res_model: "hospital.appointment",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    ["start_date", ">=", today + " 00:00:00"],
                    ["start_date", "<=", today + " 23:59:59"],
                ],
            });
        }

        if (type === "past_week") {
            const today = new Date();
            const lastWeek = new Date();
            lastWeek.setDate(today.getDate() - 7);

            const start = lastWeek.toISOString().split('T')[0];
            const end = today.toISOString().split('T')[0];

            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Past Week Appointments",
                res_model: "hospital.appointment",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    ["start_date", ">=", start + " 00:00:00"],
                    ["start_date", "<=", end + " 23:59:59"],
                ],
            });
        }

        if (type === "week") {
            const today = new Date();
            const nextWeek = new Date();
            nextWeek.setDate(today.getDate() + 7);

            const start = today.toISOString().split('T')[0];
            const end = nextWeek.toISOString().split('T')[0];

            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Next Week Appointments",
                res_model: "hospital.appointment",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    ["start_date", ">=", start + " 00:00:00"],
                    ["start_date", "<=", end + " 23:59:59"],
                ],
            });
        }
                
        if (type === "patient") {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Patients",
                res_model: "res.partner",
                views: [[false, "list"], [false, "form"]],
                domain: [["role_ids.name", "=", "Patient"]],
            });
        }

        if (type === "doctor") {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Doctors",
                res_model: "res.partner",
                views: [[false, "list"], [false, "form"]],
                domain: [["role_ids.name", "=", "Doctor"]],
            });
        }

        if (type === "appointment") {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Appointments",
                res_model: "hospital.appointment",
                views: [[false, "list"], [false, "form"]],
            });
        }
    }
}

HospitalDashboard.template = "hospital_dashboard_template";

registry.category("actions").add("hospital_dashboard", HospitalDashboard);