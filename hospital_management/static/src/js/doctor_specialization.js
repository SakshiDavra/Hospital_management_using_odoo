/** @odoo-module */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class SpecializationSnippet extends Interaction {
    static selector = ".s_specialization_list";
    dynamicContent = true;

    setup() {
        console.log("!!! SNIPPET DROPPED/LOADED !!!");
        this.start();
    }

    async start() {
        console.log("!!! SNIPPET STARTING !!!");
        await this._fetchCards();
    }

    async _fetchCards() {
        const container = this.el.querySelector(".o_specialization_container");
        if (!container) return;

        try {
            // NO LIMIT → badha data
            const result = await rpc('/hospital/specializations_html', {
                limit: 0
            });

            if (result && result.html) {
                container.innerHTML = result.html;
                console.log("!!! ALL CARDS RENDERED !!!");
            }

        } catch (e) {
            console.error("RPC Error:", e);
        }
    }
}

// register
registry.category("public.interactions").add(
    "hospital_management.specialization_list",
    SpecializationSnippet
);

registry.category("public.interactions.edit").add(
    "hospital_management.specialization_list",
    { Interaction: SpecializationSnippet }
);