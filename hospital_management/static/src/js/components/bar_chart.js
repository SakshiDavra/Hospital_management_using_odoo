/** @odoo-module **/

import { Component, onMounted, onWillUpdateProps , onWillUnmount, useRef } from "@odoo/owl";

export class BarChart extends Component {

    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        onMounted(() => {
            this.renderChart();
        });

        onWillUpdateProps((nextProps) => {
            if (this.chart) {
                this.chart.destroy();
            }

            this.props = nextProps;
            this.renderChart();
        });

        //  CLEANUP (IMPORTANT for re-render)
        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
            }
        });
    }

    renderChart() {
        const ctx = this.canvasRef.el.getContext("2d");

        const data = this.props.data || { labels: [], datasets: {} };

        // COLORS MAP
        const colors = {
            draft: '#12b2b290',
            requested: '#0e4b7d',
            confirmed: '#61185c',
            done: '#829113',
            cancel: 'rgb(119, 9, 9)',
        };

        // DYNAMIC DATASETS
        const datasets = Object.keys(data.datasets || {}).map((key) => ({
            label: key.charAt(0).toUpperCase() + key.slice(1),
            data: data.datasets[key],
            backgroundColor: colors[key] || '#999999',
            borderRadius: 10,
        }));

        this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels || [],
                datasets: datasets,
            },

            options: {
                responsive: true,
                maintainAspectRatio: false,

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
                        grid: { color: 'rgba(195, 16, 16, 0.05)' }
                    }
                },

                // CLICK HANDLER (FULL DYNAMIC)
                onClick: (evt, elements) => {
                    if (!elements.length) return;

                    const el = elements[0];
                    const index = el.index;
                    const datasetIndex = el.datasetIndex;

                    const labels = data.labels;
                    const datasetKeys = Object.keys(data.datasets);

                    const selectedLabel = labels[index];
                    const selectedState = datasetKeys[datasetIndex];

                    let start = null;
                    let end = null;

                    const today = new Date();

                    //  WEEK (Sun, Mon...)
                    if (selectedLabel.length === 3) {
                        const daysMap = {
                            Sun: 0, Mon: 1, Tue: 2,
                            Wed: 3, Thu: 4, Fri: 5, Sat: 6
                        };

                        const currentDay = today.getDay();
                        const targetDay = daysMap[selectedLabel];
                        const diff = targetDay - currentDay;

                        const selectedDate = new Date(today);
                        selectedDate.setDate(today.getDate() + diff);

                        start = selectedDate.toISOString().split('T')[0];
                        end = start;
                    }

                    // MONTH (Week 1, Week 2...)
                    else if (selectedLabel.includes("Week")) {

                        const weekNumber = parseInt(selectedLabel.split(" ")[1]);
                        const startOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);

                        const weekStart = new Date(startOfMonth);
                        weekStart.setDate(startOfMonth.getDate() + (weekNumber - 1) * 7);

                        const weekEnd = new Date(weekStart);
                        weekEnd.setDate(weekStart.getDate() + 6);

                        start = weekStart.toISOString().split('T')[0];
                        end = weekEnd.toISOString().split('T')[0];
                    }

                    // YEAR (Jan, Feb...)
                    else {
                        const monthsMap = {
                            Jan:0, Feb:1, Mar:2, Apr:3, May:4, Jun:5,
                            Jul:6, Aug:7, Sep:8, Oct:9, Nov:10, Dec:11
                        };

                        const monthIndex = monthsMap[selectedLabel];

                        const startDate = new Date(today.getFullYear(), monthIndex, 1);
                        const endDate = new Date(today.getFullYear(), monthIndex + 1, 0);

                        start = startDate.toISOString().split('T')[0];
                        end = endDate.toISOString().split('T')[0];
                    }

                    //  ACTION
                    this.env.services.action.doAction({
                        type: "ir.actions.act_window",
                        name: selectedLabel + " - " + selectedState,
                        res_model: "hospital.appointment",
                        views: [[false, "list"], [false, "form"]],
                        domain: [
                            ["state", "=", selectedState],
                            ["start_date", ">=", start + " 00:00:00"],
                            ["start_date", "<=", end + " 23:59:59"],
                        ],
                    });
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
    }
}

BarChart.template = "bar_chart_template";