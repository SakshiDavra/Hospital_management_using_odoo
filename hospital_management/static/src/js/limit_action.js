/** @odoo-module */

import { BuilderAction } from "@html_builder/core/builder_action";

export class SetRecordLimitAction extends BuilderAction {
    static id = "setRecordLimit";

    apply({ editingElement, value }) {
        // section par attribute set
        editingElement.dataset.limit = value;
    }

    isApplied({ editingElement, value }) {
        return editingElement.dataset.limit == value;
    }
}