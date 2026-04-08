/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

import { PieChart } from "./components/pie_chart";
import { BarChart } from "./components/bar_chart";
import { ShapeCanvas } from "./components/shape_canvas";
import { Layout } from "@web/search/layout";
import { CounterCard } from "./components/counter_card";

export class HospitalDashboard extends Component {

    static components = { Layout, CounterCard ,PieChart ,BarChart, ShapeCanvas};

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");

        this.openWeekDay = this.openWeekDay.bind(this);

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
                    action: "past_week",
                    loading: false,
                },
            ],

            cardData: {},     
            pieData: {},     
            chartData: {},
            filter: "week",
            chartLoading: false, 
            shapes: [],

        });

        // correct async call place
        onMounted(() => {
            this.loadCardsAndPie(); 
            this.loadBarChart(); 
        });
    }

    // proper async function
    async loadCardsAndPie() {
        try {
            const res = await this.orm.call(
                "hospital.appointment",
                "get_dashboard_cards_and_pie",
                []
            );

            if (!res) return;

            this.state.cardData = res;
            this.state.pieData = res.state_chart || {};

        } catch (error) {
            console.error("Cards/Pie Error:", error);
        }
    }

    async loadBarChart() {
        try {
            this.state.chartLoading = true;

            const res = await this.orm.call(
                "hospital.appointment",
                "get_bar_chart_data",
                [this.state.filter]
            );

            this.state.chartData = res || {};

        } catch (error) {
            console.error("Chart Error:", error);
        } finally {
            this.state.chartLoading = false;
        }
    }

    // clean action handler
    openList(type) {

        if (type === "today") {
            const today = new Date().toISOString().split('T')[0];

            return this.action.doAction({
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

        if (type === "patient") {
            return this.action.doAction({
                type: "ir.actions.act_window",
                name: "Patients",
                res_model: "res.partner",
                views: [[false, "list"], [false, "form"]],
                domain: [["role_ids.name", "=", "Patient"]],
            });
        }

        if (type === "doctor") {
            return this.action.doAction({
                type: "ir.actions.act_window",
                name: "Doctors",
                res_model: "res.partner",
                views: [[false, "list"], [false, "form"]],
                domain: [["role_ids.name", "=", "Doctor"]],
            });
        }

        if (type === "appointment") {
            return this.action.doAction({
                type: "ir.actions.act_window",
                name: "Appointments",
                res_model: "hospital.appointment",
                views: [[false, "list"], [false, "form"]],
            });
        }

        if (type === "week" || type === "past_week") {
            const today = new Date();
            const other = new Date();

            if (type === "week") {
                other.setDate(today.getDate() + 7);
            } else {
                other.setDate(today.getDate() - 7);
            }

            const start = type === "week" ? today : other;
            const end = type === "week" ? other : today;

            return this.action.doAction({
                type: "ir.actions.act_window",
                name: "Appointments",
                res_model: "hospital.appointment",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    ["start_date", ">=", start.toISOString().split('T')[0] + " 00:00:00"],
                    ["start_date", "<=", end.toISOString().split('T')[0] + " 23:59:59"],
                ],
            });
        }
    }
    openStatusList(status) {
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: status + " Appointments",
            res_model: "hospital.appointment",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "=", status]],
        });
    }
    openWeekDay(label, status = null) {
        const today = new Date();

        let startDate, endDate;

        // ================= WEEK =================
        if (this.state.filter === "week") {
            const daysMap = {
                Mon: 1, Tue: 2, Wed: 3, Thu: 4,
                Fri: 5, Sat: 6, Sun: 0
            };

            const targetDay = daysMap[label];
            const currentDay = today.getDay();

            const diff = targetDay - currentDay;

            const selectedDate = new Date(today);
            selectedDate.setDate(today.getDate() + diff);

            startDate = selectedDate.toISOString().split('T')[0] + " 00:00:00";
            endDate   = selectedDate.toISOString().split('T')[0] + " 23:59:59";
        }

        // ================= MONTH =================
        else if (this.state.filter === "month") {
            const day = parseInt(label);

            const selectedDate = new Date(today.getFullYear(), today.getMonth(), day);

            startDate = selectedDate.toISOString().split('T')[0] + " 00:00:00";
            endDate   = selectedDate.toISOString().split('T')[0] + " 23:59:59";
        }

        // ================= YEAR =================
        else if (this.state.filter === "year") {
            const month = parseInt(label);

            const start = new Date(today.getFullYear(), month - 1, 1);
            const end   = new Date(today.getFullYear(), month, 0);

            startDate = start.toISOString().split('T')[0] + " 00:00:00";
            endDate   = end.toISOString().split('T')[0] + " 23:59:59";
        }

        // ================= DOMAIN BUILD =================
        const domain = [
            ["start_date", ">=", startDate],
            ["start_date", "<=", endDate],
        ];

        // 🔥 ADD STATUS FILTER (only if clicked on stacked part)
        if (status) {
            domain.push(["state", "=", status]);
        }

        return this.action.doAction({
            type: "ir.actions.act_window",
            name: status 
                ? `${label} (${status}) Appointments`
                : `${label} Appointments`,
            res_model: "hospital.appointment",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
        });
    }
    onFilterChange(ev) {
        this.state.filter = ev.target.value;
        this.state.chartData = {};  
        this.loadBarChart();  
    }
    onShapesUpdate(shapes) {
        console.log("Shapes updated:", shapes);
        this.state.shapes = shapes;
    }
}

HospitalDashboard.template = "hospital_dashboard_template";

//  FINAL registration
registry.category("actions").add("hospital_dashboard", HospitalDashboard);