/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";

export class BarChart extends Component {

    setup() {
        this.canvasRef = useRef("canvas");

        onMounted(() => {
            const ctx = this.canvasRef.el.getContext("2d");

            // Gradient (premium look)
            const gradient = ctx.createLinearGradient(0, 0, 0, 300);
            gradient.addColorStop(0, "#6c1b22");
            gradient.addColorStop(1, "#db849f");

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: this.props.data.labels,
                    datasets: [{
                        data: this.props.data.values,
                        backgroundColor: gradient,
                        borderRadius: 15,
                        barThickness: 45,
                        categoryPercentage: 0.7,
                        barPercentage: 0.8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    onClick: (evt, elements) => {
                        if (elements.length > 0) {

                            const index = elements[0].index;

                            // selected day label (Sun, Mon...)
                            const selectedDay = this.props.data.labels[index];

                            // date calculate (IMPORTANT)
                            const today = new Date();
                            const currentDay = today.getDay(); // 0=Sun

                            const daysMap = {
                                Sun: 0, Mon: 1, Tue: 2,
                                Wed: 3, Thu: 4, Fri: 5, Sat: 6
                            };

                            const targetDay = daysMap[selectedDay];

                            const diff = targetDay - currentDay;
                            const selectedDate = new Date(today);
                            selectedDate.setDate(today.getDate() + diff);

                            const start = selectedDate.toISOString().split('T')[0];
                            const end = start;

                            // open filtered records
                            this.env.services.action.doAction({
                                type: "ir.actions.act_window",
                                name: selectedDay + " Appointments",
                                res_model: "hospital.appointment",
                                views: [[false, "list"], [false, "form"]],
                                domain: [
                                    ["start_date", ">=", start + " 00:00:00"],
                                    ["start_date", "<=", end + " 23:59:59"],
                                ],
                            });
                        }
                    },

                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: '#222',
                            titleColor: '#fff',
                            bodyColor: '#fff'
                        }
                    },

                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: {
                                color: '#888'
                            }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1,  
                                color: '#888'
                            },
                            grid: {
                                color: 'rgba(0,0,0,0.05)'
                            }
                        }
                    }
                }
            });
        });
    }
}

BarChart.template = "bar_chart_template";