/** @odoo-module **/

import { Component, onMounted, onWillUnmount, onWillUpdateProps, useRef } from "@odoo/owl";

export class BarChart extends Component {
    setup() {
        this.canvasRef = useRef("canvas");
        this.chart = null;

        onMounted(() => this.renderChart());

        onWillUpdateProps((nextProps) => {
            this.destroyChart();

            // important delay
            setTimeout(() => {
                this.renderChart(nextProps);
            });
        });

        onWillUnmount(() => {
            this.destroyChart();
        });
    }

    destroyChart() {
        if (this.chart) {
            this.chart.destroy();
            this.chart = null;
        }

        // canvas reset (VERY IMPORTANT)
        if (this.canvasRef.el) {
            this.canvasRef.el.width = this.canvasRef.el.width;
        }
    }

    renderChart(props = this.props) {
        const data = props.data || {};

        if (!data || Object.keys(data).length === 0) return;

        const ctx = this.canvasRef.el.getContext("2d");

        const labels = data.labels || [];
        const datasets = data.datasets || [];

        console.log("Chart Labels:", labels); 

        this.chart = new Chart(ctx, {
            type: "bar",
            data: {
                labels: labels,
                datasets: datasets.map(ds => ({
                    label: {
                        draft: "Draft",
                        requested: "Requested",
                        confirmed: "Confirmed",
                        done: "Done",
                        in_consultation: "In Consultation",
                        cancel: "Cancelled",
                    }[ds.label] || ds.label,
                    data: ds.data,
                    backgroundColor: {
                        draft: "#602577",
                        requested: "#957701",
                        confirmed: "#04568c",
                        done: "#068039",
                        cancel: "#93190c",
                    }[ds.label] || "#999",
                })),
            },
            options: {

                responsive: true,
                maintainAspectRatio: false,

                plugins: {
                    legend: {
                        display: true, 
                    },
                },

                scales: {
                    x: {
                        stacked: true,
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                    }
                },

                onClick: (evt, elements, chart) => {
                    const points = chart.getElementsAtEventForMode(
                        evt,
                        'nearest',
                        { intersect: true },
                        true
                    );

                    if (points.length > 0 && this.props.onClick) {
                        const firstPoint = points[0];

                        const index = firstPoint.index;
                        const datasetIndex = firstPoint.datasetIndex;

                        const label = labels[index];
                        const dataset = datasets[datasetIndex];

                        const status = dataset.label;

                        console.log("Clicked:", label, status);

                        this.props.onClick(label, status);
                    }
                },

                onHover: (evt, elements) => {
                    evt.native.target.style.cursor = elements.length ? "pointer" : "default";
                },
            },
        });
    }
}

BarChart.template = "hospital.BarChart";