/** @odoo-module **/

import { Component, onMounted, useRef } from "@odoo/owl";

export class BarChart extends Component {

    setup() {
        this.canvasRef = useRef("canvas");

        onMounted(() => {
            const ctx = this.canvasRef.el.getContext("2d");

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: this.props.data.labels,

                    datasets: [
                        {
                            label: 'Draft',
                            data: this.props.data.datasets.draft,
                            backgroundColor: '#12b2b290',
                            borderRadius: 10,
                        },
                        {
                            label: 'Requested',
                            data: this.props.data.datasets.requested,
                            backgroundColor: '#0e4b7d',
                            borderRadius: 10,
                        },
                        {
                            label: 'Confirmed',
                            data: this.props.data.datasets.confirmed,
                            backgroundColor: '#61185c',
                            borderRadius: 10,
                        },
                        {
                            label: 'Done',
                            data: this.props.data.datasets.done,
                            backgroundColor: '#829113',
                            borderRadius: 10,
                        },
                        {
                            label: 'Cancelled',
                            data: this.props.data.datasets.cancel,
                            backgroundColor: 'rgb(119, 9, 9)',
                            borderRadius: 10,
                        }
                    ]
                },

                options: {
                    responsive: true,
                    maintainAspectRatio: false,

                    // 🔥 STACK ENABLE
                    scales: {
                        x: {
                            stacked: true,
                            grid: { display: false },
                            ticks: { color: '#888' }
                        },
                        y: {
                            stacked: true,
                            beginAtZero: true,
                            ticks: { stepSize: 1, color: '#888' },
                            grid: { color: 'rgba(0,0,0,0.05)' }
                        }
                    },

                    //  CLICK EVENT (STATE + DAY)
                     onClick: (evt, elements) => {
                        if (elements.length > 0) {

                            const element = elements[0];
                            const index = element.index;
                            const datasetIndex = element.datasetIndex;

                            const selectedDay = this.props.data.labels[index];

                            const states = ['draft', 'requested', 'confirmed', 'done', 'cancel'];
                            const selectedState = states[datasetIndex];

                            const today = new Date();
                            const currentDay = today.getDay();

                            const daysMap = {
                                Sun: 0, Mon: 1, Tue: 2,
                                Wed: 3, Thu: 4, Fri: 5, Sat: 6
                            };

                            const targetDay = daysMap[selectedDay];
                            const diff = targetDay - currentDay;

                            const selectedDate = new Date(today);
                            selectedDate.setDate(today.getDate() + diff);

                            const start = selectedDate.toISOString().split('T')[0];

                            this.env.services.action.doAction({
                                type: "ir.actions.act_window",
                                name: selectedDay + " - " + selectedState,
                                res_model: "hospital.appointment",
                                views: [[false, "list"], [false, "form"]],
                                domain: [
                                    ["state", "=", selectedState],
                                    ["start_date", ">=", start + " 00:00:00"],
                                    ["start_date", "<=", start + " 23:59:59"],
                                ],
                            });
                        }
                    },

                    plugins: {
                        legend: {
                            display: true,
                            position: 'bottom'
                        },
                        tooltip: {
                            backgroundColor: '#222',
                            titleColor: '#fff',
                            bodyColor: '#fff'
                        }
                    }
                }
            });
        });
    }
}

BarChart.template = "bar_chart_template";