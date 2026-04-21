/** @odoo-module */

import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";

import { SpecializationOption } from "./specialization_option";
import { SetRecordLimitAction } from "./limit_action";

export class SpecializationPlugin extends Plugin {
    static id = "specializationPlugin";

    resources = {
        builder_actions: {
            SetRecordLimitAction,
        },
        builder_options: withSequence(1000, SpecializationOption),
    };
}

registry.category("website-plugins").add(
    "specializationPlugin",
    SpecializationPlugin
);