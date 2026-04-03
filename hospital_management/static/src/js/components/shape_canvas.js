/** @odoo-module **/

import { Component, useRef } from "@odoo/owl";

export class ShapeCanvas extends Component {

    setup() {
        this.canvasRef = useRef("canvas");

        this.currentShape = null;
        this.currentColor = "#ff0000";

        this.shapes = [];

        this.drawMode = false;   // control drawing
    }

    // DRAW ALL SHAPES
    drawAllShapes() {
        const canvas = this.canvasRef.el;
        const ctx = canvas.getContext("2d");

        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();

        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;

        ctx.resetTransform();
        ctx.scale(dpr, dpr);

        const w = rect.width;
        const h = rect.height;

        ctx.clearRect(0, 0, w, h);

        const size = Math.min(w, h) / 2;  

        this.shapes.forEach(shape => {

            ctx.beginPath();
            ctx.lineWidth = 2;

            // ================= SHAPES =================

            if (shape.type === "square") {
                ctx.rect(shape.x - size/2, shape.y - size/2, size, size);
            }

            else if (shape.type === "circle") {
                ctx.arc(shape.x, shape.y, size/2, 0, Math.PI * 2);
            }

            else if (shape.type === "triangle") {
                ctx.moveTo(shape.x, shape.y - size/2);
                ctx.lineTo(shape.x - size/2, shape.y + size/2);
                ctx.lineTo(shape.x + size/2, shape.y + size/2);
                ctx.closePath();
            }

            else if (shape.type === "pentagon") {
                const r = size/2;

                for (let i = 0; i < 5; i++) {
                    const angle = (i * 2 * Math.PI / 5) - Math.PI / 2;
                    const px = shape.x + r * Math.cos(angle);
                    const py = shape.y + r * Math.sin(angle);

                    if (i === 0) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                }
                ctx.closePath();
            }

            // fill only if true
            if (shape.filled) {
                ctx.fillStyle = shape.color;
                ctx.fill();
            }

            ctx.stroke();
        });
    }

    // CLICK HANDLER
    onCanvasClick(ev) {
        const canvas = this.canvasRef.el;
        const rect = canvas.getBoundingClientRect();

        const x = ev.clientX - rect.left;
        const y = ev.clientY - rect.top;

        //  check if clicked on existing shape
        let clickedShape = this.shapes.find(shape => {
            const dx = x - shape.x;
            const dy = y - shape.y;
            return Math.sqrt(dx*dx + dy*dy) < 60;
        });

        if (clickedShape) {
            // fill existing shape
            clickedShape.filled = true;
            clickedShape.color = this.currentColor;
        }

        // draw only when drawMode ON
        else if (this.drawMode && this.currentShape) {

            this.shapes.push({
                type: this.currentShape,
                x: x,
                y: y,
                color: this.currentColor,
                filled: false
            });

            this.drawMode = false;   // auto OFF after 1 draw
        }

        this.drawAllShapes();
    }

    // SHAPE SELECT
    onShapeChange(ev) {
        const value = ev.target.value;

        if (!value) return;

        this.currentShape = value;
        this.drawMode = true;   // enable draw for 1 time
    }

    // COLOR SELECT
    onColorChange(ev) {
        this.currentColor = ev.target.value;
    }
}

ShapeCanvas.template = "shape_canvas_template";