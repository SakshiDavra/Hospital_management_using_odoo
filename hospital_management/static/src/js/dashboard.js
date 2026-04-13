/** @odoo-module **/
import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { PieChart } from "./components/pie_chart";
import { BarChart } from "./components/bar_chart";
import { ShapeCanvas } from "./components/shape_canvas";
import { TodoList } from "./components/todo_list";
import { TopDoctors } from "./components/top_doctors";
import { Layout } from "@web/search/layout";
import { CounterCard } from "./components/counter_card";

export class HospitalDashboard extends Component {

    static components = { Layout, CounterCard ,PieChart ,BarChart, ShapeCanvas, TodoList ,TopDoctors};
    formatLocalDate(date) {
        const year  = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day   = String(date.getDate()).padStart(2, '0');

        return `${year}-${month}-${day}`;
    }
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
            //shapes: [],
            isLoading: true, 

        });

        // correct async call place
        onMounted(async () => {
            this.state.isLoading = true;

            await Promise.all([
                this.loadCardsAndPie(),
                this.loadBarChart()
            ]);

            this.state.isLoading = false;   
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
                context: {
                    create: false,   //cards  hide New button
                    edit: false,
                    delete: false
                }
            });
        }

        if (type === "patient") {
            return this.action.doAction("hospital_management.action_patient_custom",
            {
                additionalContext: {
                    create: false,
                    edit: false,
                    delete: false
                }
            });
        }

        if (type === "doctor") {
            return this.action.doAction("hospital_management.action_doctor_custom",
            {
                additionalContext: {
                    create: false,
                    edit: false,
                    delete: false
                }
            });
        }

        if (type === "appointment") {
            return this.action.doAction({
                type: "ir.actions.act_window",
                name: "Appointments",
                res_model: "hospital.appointment",
                views: [[false, "list"], [false, "form"]],
                context: {
                    create: false,   //cards  hide New button
                    edit: false,
                    delete: false
                }
            });
        }

        if (type === "week" || type === "past_week") {

            const today = new Date();

            // STEP 1: current week Sunday
            const currentDay = today.getDay(); // 0 = Sun
            const currentWeekStart = new Date(today);
            currentWeekStart.setDate(today.getDate() - currentDay);

            const currentWeekEnd = new Date(currentWeekStart);
            currentWeekEnd.setDate(currentWeekStart.getDate() + 6);

            let start, end;

            if (type === "week") {
                // NEXT WEEK
                start = new Date(currentWeekStart);
                start.setDate(start.getDate() + 7);

                end = new Date(currentWeekEnd);
                end.setDate(end.getDate() + 7);
            } else {
                // PAST WEEK
                start = new Date(currentWeekStart);
                start.setDate(start.getDate() - 7);

                end = new Date(currentWeekEnd);
                end.setDate(end.getDate() - 7);
            }

            return this.action.doAction({
                type: "ir.actions.act_window",
                name: type === "week" ? "Next Week Appointments" : "Past Week Appointments",
                res_model: "hospital.appointment",
                views: [[false, "list"], [false, "form"]],
                domain: [
                    ["start_date", ">=", start.toISOString().split('T')[0] + " 00:00:00"],
                    ["start_date", "<=", end.toISOString().split('T')[0] + " 23:59:59"],
                ],
                context: {
                    create: false,   //cards  hide New button
                    edit: false,
                    delete: false
                }
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
            context: {
                create: false,   // pie hide New button
                    edit: false,
                    delete: false
            }
        });
    }
    openWeekDay(label, status = null) {
        const today = new Date();

        let startDate, endDate;

        // ================= WEEK =================
        if (this.state.filter === "week") {
            const daysMap = {
                Sun: 0, Mon: 1, Tue: 2, Wed: 3,
                Thu: 4, Fri: 5, Sat: 6
            };

            const targetDay = daysMap[label];
            const currentDay = today.getDay();

            const diff = targetDay - currentDay;

            const selectedDate = new Date(today);
            selectedDate.setDate(today.getDate() + diff);

            const start = new Date(selectedDate);
            start.setHours(0, 0, 0, 0);

            const end = new Date(selectedDate);
            end.setHours(23, 59, 59, 999);

            startDate = start.toISOString().slice(0, 19).replace('T', ' ');
            endDate   = end.toISOString().slice(0, 19).replace('T', ' ');
        }

        else if (this.state.filter === "month") {

            const weekRanges = this.state.chartData.week_ranges || [];

            const selected = weekRanges.find(w => w.label === label);

            if (!selected) {
                console.error("Week not found", label, weekRanges);
                return;
            }

            startDate = selected.start + " 00:00:00";
            endDate   = selected.end + " 23:59:59";
        }

        // ================= YEAR =================
        else if (this.state.filter === "year") {
            const month = parseInt(label);

            const start = new Date(today.getFullYear(), month - 1, 1);
            const end   = new Date(today.getFullYear(), month, 0);

            start.setHours(0, 0, 0, 0);
            end.setHours(23, 59, 59, 999);

            startDate = start.toISOString().slice(0, 19).replace('T', ' ');
            endDate   = end.toISOString().slice(0, 19).replace('T', ' ');
        }

        // ================= DOMAIN =================
        const domain = [
            ["start_date", ">=", startDate],
            ["start_date", "<=", endDate],
        ];

        if (status) {
            domain.push(["state", "=", status]);
        }

        console.log("FINAL DOMAIN:", domain);

        return this.action.doAction({
            type: "ir.actions.act_window",
            name: status
                ? `${label} (${status}) Appointments`
                : `${label} Appointments`,
            res_model: "hospital.appointment",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            context: {
                create: false   // hide New button
            }
        });
    }
    
    onFilterChange(ev) {
        this.state.filter = ev.target.value;
        this.state.chartData = {};  
        this.loadBarChart();  
    }

}

HospitalDashboard.template = "hospital_dashboard_template";

//  FINAL registration
registry.category("actions").add("hospital_dashboard", HospitalDashboard);