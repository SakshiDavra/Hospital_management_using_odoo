/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

export class ShapeCanvas extends Component {

    setup() {
        this.state = useState({
            shapes: this.props.shapes || [],
            currentShape: null,
            currentColor: "#ff0000",
            drawMode: false,
        });
    }

    // ================= CLICK =================
    onCanvasClick(ev) {
        const svg = ev.currentTarget; 

        const rect = svg.getBoundingClientRect();

        const x = ev.clientX - rect.left;
        const y = ev.clientY - rect.top;

        let shapes = [...this.state.shapes];

        const index = shapes.findIndex(s => {
            const dx = x - s.x;
            const dy = y - s.y;
            return Math.sqrt(dx * dx + dy * dy) < 40;
        });

        // FILL SHAPE
        if (index !== -1) {
            shapes[index] = {
                ...shapes[index],
                filled: true,
                color: this.state.currentColor
            };
        }

        // ADD NEW SHAPE
        else if (this.state.drawMode && this.state.currentShape) {
            shapes.push({
                type: this.state.currentShape,
                x,
                y,
                color: this.state.currentColor,
                filled: false
            });

            this.state.drawMode = false;
        }

        this.state.shapes = shapes;

        this.props.onUpdate && this.props.onUpdate(shapes);
    }

    // ================= CONTROLS =================
    setShape(shape) {
        this.state.currentShape = shape;
        this.state.drawMode = true;
    }

    setColor(ev) {
        this.state.currentColor = ev.target.value;
    }

    clearCanvas() {
        this.state.shapes = [];
        this.props.onUpdate && this.props.onUpdate([]);
    }
}

ShapeCanvas.template = "shape_canvas_template";