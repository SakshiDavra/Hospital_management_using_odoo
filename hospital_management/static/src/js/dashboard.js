/** @odoo-module **/

import { Component, useState ,onMounted  } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";

import { Layout } from "@web/search/layout";
import { CounterCard } from "./components/counter_card";
import { PieChart } from "./components/pie_chart";
import { BarChart } from "./components/bar_chart";
import { ShapeCanvas } from "./components/shape_canvas";

export class HospitalDashboard extends Component {

    static components = { Layout, CounterCard, PieChart, BarChart, ShapeCanvas,};

    setup() {
        this.action = useService("action");

        this.state = useState({
            cards: [
                {
                    title: "Total Patients",
                    key: "patients",
                    bg: "bg-gradient-blue",
                    icon: "fa fa-user",
                    action: "patient"
                },
                {
                    title: "Total Doctors",
                    key: "doctors",
                    bg: "bg-gradient-green",
                    icon: "fa fa-user-md",
                    action: "doctor"
                },
                {
                    title: "Total Appointments",
                    key: "appointments",
                    bg: "bg-gradient-yellow",
                    icon: "fa fa-calendar",
                    action: "appointment"
                },
                {
                    title: "Today's Appointments",
                    key: "today_appointments",
                    bg: "bg-gradient-purple",
                    icon: "fa fa-calendar",
                    action: "today"
                },
                {
                    title: "Next Week",
                    key: "week_appointments",
                    bg: "bg-gradient-blue",
                    icon: "fa fa-calendar-check-o",
                    action: "week"
                },
                {
                    title: "Past Week",
                    key: "past_week",
                    bg: "bg-gradient-red",
                    icon: "fa fa-history",
                    action: "past_week"
                },
            ],

            data: {},
            state_data: [],
            filter: "week",
            chart_data: {},
            loading: true,
        });
        // LAZY LOADING
        onMounted(async () => {
            await this.loadDashboardData(true);  // first load
        });

    }
    async loadDashboardData(isInitial = false) {

        // loader ONLY first time
        if (isInitial) {
            this.state.loading = true;
        }

        const res = await rpc("/hospital/dashboard/data", {
            filter: this.state.filter,
        });

        this.state.data = res;
        this.state.state_data = res.state_data;
        this.state.chart_data = res.chart;

        if (isInitial) {
            this.state.loading = false;
        }
    }

    // DROPDOWN CHANGE
    async onFilterChange(ev) {
        ev.preventDefault();

        this.state.filter = ev.target.value;

        // DO NOT use loading
        const res = await rpc("/hospital/dashboard/data", {
            filter: this.state.filter,
        });

        // ONLY update chart
        this.state.chart_data = res.chart;
    }

    // CARD CLICK ACTIONS
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