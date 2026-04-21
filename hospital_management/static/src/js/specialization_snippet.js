/** @odoo-module */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class SpecializationSnippet extends Interaction {
    static selector = ".s_specialization_list_snippets";

    setup() {
        this.orm = this.env.services.orm;
    }

    async start() {
        this.loadData();
    }

    async loadData() {
        const limit = parseInt(this.el.dataset.limit) || 4;

        const records = await this.orm.searchRead(
            "hospital.specialization",
            [],
            ["name"],
            { limit }
        );

        let html = "";

        records.forEach(rec => {
            html += `
                <div class="col-lg-3 col-md-4 col-sm-6 mb-3">
                    <div class="card p-3 text-center">
                        <h5>${rec.name}</h5>
                    </div>
                </div>
            `;
        });

        this.el.querySelector(".o_specialization_container").innerHTML = html;
    }
}

registry.category("public.interactions").add(
    "hospital.specialization_snippet",
    SpecializationSnippet
);
registry.category("public.interactions.edit").add(
    "hospital.specialization_snippet",
     {Interaction:SpecializationSnippet}
);