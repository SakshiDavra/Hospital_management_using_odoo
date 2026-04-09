/** @odoo-module **/
console.log("TopDoctors file loaded");
import { Component, useState, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class TopDoctors extends Component {

    setup() {
        this.orm = useService("orm");

        this.state = useState({
            doctors: [],
            loading: true,
        });

        onMounted(async () => {
            await this.loadDoctors();
        });
    }

    async loadDoctors() {
        this.state.loading = true;

        try {
            const res = await this.orm.call(
                "hospital.appointment",
                "get_top_doctors",
                []
            );

            this.state.doctors = res || [];

        } catch (error) {
            console.error("TopDoctors Error:", error);
        } finally {
            this.state.loading = false;
        }
    }
}

// VERY IMPORTANT (typo na hoy)
TopDoctors.template = "hospital.TopDoctors";