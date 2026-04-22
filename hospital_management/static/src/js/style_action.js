/** @odoo-module */

import { BuilderAction } from "@html_builder/core/builder_action";

export class SetTemplateStyle extends BuilderAction {
    static id = "setTemplateStyle";

    apply({ editingElement, value }) {
        editingElement.dataset.style = value;
    }

    isApplied({ editingElement, value }) {
        return editingElement.dataset.style === value;
    }
}