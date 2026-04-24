/** @odoo-module */

import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";

export class SpecializationSnippet extends Interaction {
    static selector = ".s_specialization_list_snippets";

    setup() {
        this.orm = this.env.services.orm;

        this.allRecords = [];
        this.expanded = false;
        this.defaultLimit = 4;
        this.style = "Style-Default";
    }

    start() {
        this.loadData();
        this.observeChanges();
    }

    observeChanges() {
        const observer = new MutationObserver(() => {
            this.loadData();
        });

        observer.observe(this.el, {
            attributes: true,
            attributeFilter: ["data-limit", "data-style"],
        });
    }

    async loadData() {
        this.defaultLimit = parseInt(this.el.dataset.limit) || 4;
        this.style = this.el.dataset.style || "Style-Default";

        this.expanded = false;

        if (this.style === "Style-Listview") {
            this.allRecords = await this.orm.searchRead(
                "hospital.specialization",
                [],
                ["name"]
            );
        } else {
            this.allRecords = await this.orm.searchRead(
                "hospital.specialization",
                [],
                ["name"],
                { limit: this.defaultLimit }
            );
        }

        this.renderData();
    }

    renderData() {
        let recordsToShow;

        if (this.style === "Style-Listview") {
            recordsToShow = this.expanded
                ? this.allRecords
                : this.allRecords.slice(0, this.defaultLimit);
        } else {
            recordsToShow = this.allRecords;
        }

        const html = renderToElement("hospital.SpecializationGrid", {
            records: recordsToShow,
            style: this.style,
            showToggle: this.style === "Style-Listview",
            expanded: this.expanded,
            total: this.allRecords.length,
            limit: this.defaultLimit,
        });

        const container = this.el.querySelector(".o_specialization_container");
        container.innerHTML = "";
        container.replaceChildren(html);

        this.bindButtons();
    }

    bindButtons() {
        const showMoreBtn = this.el.querySelector(".show-more-btn");
        const showLessBtn = this.el.querySelector(".show-less-btn");

        if (showMoreBtn) {
            showMoreBtn.addEventListener("click", () => {
                this.expanded = true;
                this.renderData();
            });
        }

        if (showLessBtn) {
            showLessBtn.addEventListener("click", () => {
                this.expanded = false;
                this.renderData();
            });
        }
    }
}

registry.category("public.interactions").add(
    "hospital.specialization_snippet",
    SpecializationSnippet
);

registry.category("public.interactions.edit").add(
    "hospital.specialization_snippet",
    { Interaction: SpecializationSnippet }
);
