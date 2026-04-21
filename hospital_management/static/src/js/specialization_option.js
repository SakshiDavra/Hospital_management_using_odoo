/** @odoo-module */

import { BaseOptionComponent } from "@html_builder/core/utils";

export class SpecializationOption extends BaseOptionComponent {
    static template = "hospital.specialization_option";

    //  MUST ADD THIS
    static selector = ".s_specialization_list_snippets";
}