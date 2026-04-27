/** @odoo-module **/

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(ProductScreen.prototype, {
    setup() {
        super.setup();

        onMounted(() => {
            const width = this.pos.config.product_card_width || 150;
            const height = this.pos.config.product_card_height || 200;
            const fontSize = this.pos.config.product_font_size || 14;

            // 🔥 AREA CALCULATION
            const imageHeight = Math.floor(height * 0.7);
            const textHeight = Math.floor(height * 0.3);

            const oldStyle = document.getElementById("dynamic-pos-style");
            if (oldStyle) oldStyle.remove();

            const style = document.createElement("style");
            style.id = "dynamic-pos-style";

            style.innerHTML = `
                /* GRID */
                .pos .product-list {
                    grid-template-columns: repeat(auto-fill, minmax(${width}px, 1fr)) !important;
                }

                /* CARD */
                .pos .product {
                    height: ${height}px !important;
                    position: relative;
                    overflow: hidden;
                    padding: 0;
                }

                /* IMAGE AREA (TOP 70%) */
                .pos .product-img {
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 70%;
                    overflow: hidden;
                }

                /* IMAGE */
                .pos .product-img img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }

                /* TEXT AREA (BOTTOM 30%) */
                .pos .product-name {
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    width: 100%;
                    height: 30%;
                    font-size: ${fontSize}px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    padding: 5px;
                    background: white;
                }
            `;

            document.head.appendChild(style);
        });
    },
});