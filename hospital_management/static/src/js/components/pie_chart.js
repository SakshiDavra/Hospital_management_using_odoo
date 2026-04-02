/** @odoo-module **/

import { Component, onMounted, onWillStart, useRef } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class PieChart extends Component {

    setup() {
        this.canvasRef = useRef("canvas");

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
        });

        onMounted(() => {
            this.renderChart();
        });
    }

    renderChart() {

        const canvas = this.canvasRef.el;
        if (!canvas) return;

        const ctx = canvas.getContext("2d");

        const stateMap = {
            draft: "Draft",
            requested: "Requested",
            confirmed: "Confirmed",
            done: "Done",
            cancel: "Cancelled"
        };

        const labels = this.props.data.map(d => stateMap[d.state]);
        const values = this.props.data.map(d => d.state_count);

        const total = values.reduce((a, b) => a + b, 0);

        //  Gradient colors (same as cards)
        const gradients = [
            ctx.createLinearGradient(0, 0, 200, 200),
            ctx.createLinearGradient(0, 0, 200, 200),
            ctx.createLinearGradient(0, 0, 200, 200),
            ctx.createLinearGradient(0, 0, 200, 200),
            ctx.createLinearGradient(0, 0, 200, 200),
        ];

        gradients[0].addColorStop(0, "#3888ce");
        gradients[0].addColorStop(1, "#0b5054");

        gradients[1].addColorStop(0, "#4ee27f");
        gradients[1].addColorStop(1, "#2e8766");

        gradients[2].addColorStop(0, "#af9029");
        gradients[2].addColorStop(1, "#d8785e");

        gradients[3].addColorStop(0, "#5f3cb0");
        gradients[3].addColorStop(1, "#e74abb");

        gradients[4].addColorStop(0, "#a13446");
        gradients[4].addColorStop(1, "#571732");

        //  Center Text Plugin
        const centerText = {
            id: 'centerText',
            beforeDraw(chart) {
                const { width, height } = chart;
                const ctx = chart.ctx;

                ctx.save();

                ctx.font = "bold 22px sans-serif";
                ctx.fillStyle = "#222";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(total, width / 2, height / 2 + 10);

                ctx.font = "12px sans-serif";
                ctx.fillStyle = "#777";
                ctx.fillText("Appointments", width / 2, height / 2 + 30);

                ctx.restore();
            }
        };

        new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: gradients,
                    borderColor: '#fff',
                    borderWidth: 2,
                    hoverOffset: 12
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',

                onClick: (evt, elements) => {
                    if (elements.length > 0) {

                        const index = elements[0].index;

                        // state key direct data mathi
                        const selectedState = this.props.data[index].state;

                        // open filtered records
                        this.env.services.action.doAction({
                            type: "ir.actions.act_window",
                            name: "Appointments",
                            res_model: "hospital.appointment",
                            views: [[false, "list"], [false, "form"]],
                            domain: [["state", "=", selectedState]],
                        });
                    }
                },

                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            boxWidth: 12,
                            padding: 15,
                            color: '#555'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ": " + context.raw;
                            }
                        }
                    }
                },

                animation: {
                    duration: 1000
                }
            },
            plugins: [centerText]
        });
    }
}

PieChart.template = "pie_chart_template";