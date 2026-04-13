/** @odoo-module **/

import { Component, onMounted, onWillUnmount, onWillUpdateProps, useRef } from "@odoo/owl";

export class PieChart extends Component {
    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        onMounted(() => {
            this.renderChart();
        });

        // ✅ Proper re-render
        onWillUpdateProps((nextProps) => {
            if (JSON.stringify(nextProps.data) === JSON.stringify(this.props.data)) {
                return; // 🔥 no re-render
            }

            if (this.chart) {
                this.chart.destroy();
                this.chart = null;
            }

            setTimeout(() => {
                this.renderChart(nextProps);
            });
        });

        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
                this.chart = null;
            }
        });
    }

    renderChart(props = this.props) {
        const data = props.data || {};

        // No data handling
        if (!data || Object.keys(data).length === 0) {
            return;
        }

        // Canvas null check
        if (!this.canvasRef.el) return;

        const ctx = this.canvasRef.el.getContext("2d");

        const rawLabels = Object.keys(data);

        const labels = rawLabels.map(label => ({
            draft: "Draft",
            requested: "Requested",
            confirmed: "Confirmed",
            done: "Done",
            in_consultation: "In Consultation",
            cancel: "Cancelled",
        }[label] || label));
        const values = Object.values(data);

        const total = values.reduce((a, b) => a + b, 0);

        // Responsive Center Text
        const centerText = {
            id: "centerText",
            beforeDraw: (chart) => {
                if (!props.showCenterTotal) return;

                const { width, height } = chart;
                const ctx = chart.ctx;

                ctx.save();

                const fontSize = Math.min(width, height) / 10;

                // TOTAL
                ctx.font = `bold ${fontSize}px sans-serif`;
                ctx.fillStyle = "#333";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(total, width / 2, height / 2 - fontSize / 3);

                // LABEL
                ctx.font = `${fontSize / 2.5}px sans-serif`;
                ctx.fillStyle = "#888";

                const title = props.centerLabel || "Total";
                ctx.fillText(title, width / 2, height / 2 + fontSize / 2);

                ctx.restore();
            },
        };

        this.chart = new Chart(ctx, {
            type: props.type || "doughnut",
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: props.colors || [
                        "#04568c",
                        "#957701",
                        "#068039",
                        "#93190c",
                        "#602577"
                    ],
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: props.cutout || "60%",

                plugins: {
                    legend: {
                        position: props.legendPosition || "bottom",
                    },
                },

                onClick: (evt, elements) => {
                    if (elements.length > 0 && props.onClick) {
                        const index = elements[0].index;
                        const label = rawLabels[index];
                        props.onClick(label);
                    }
                },
            },
            plugins: [centerText],
        });
    }
}

PieChart.template = "hospital.PieChart";